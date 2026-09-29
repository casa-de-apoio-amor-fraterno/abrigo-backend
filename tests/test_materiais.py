from app.core.security import criar_token_acesso
from app.features.materiais.models import Material


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_exige_login(client):
    resposta = client.get("/api/materiais")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/materiais", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_descricao(client, db_session, usuario_legado, local_casa):
    db_session.add_all(
        [
            Material(descricao="Cadeira de rodas", situacao="Disponível", id_local=local_casa.id),
            Material(descricao="Muletas", situacao="Disponível", id_local=local_casa.id),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/materiais", params={"busca": "cadeira"}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["descricao"] == "Cadeira de rodas"


def test_listar_apenas_disponiveis_emprestimo(client, db_session, usuario_legado, local_casa):
    db_session.add_all(
        [
            Material(
                descricao="Cadeira de rodas",
                situacao="Disponível",
                id_local=local_casa.id,
                disponivel_emprestimo=True,
            ),
            Material(
                descricao="Impressora", situacao="Disponível", id_local=local_casa.id, disponivel_emprestimo=False
            ),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/materiais",
        params={"apenas_disponiveis_emprestimo": True},
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["descricao"] == "Cadeira de rodas"


def test_listar_nao_traz_inativo(client, db_session, usuario_legado, local_casa):
    db_session.add(Material(descricao="Inutilizado", situacao="Inutilizado", id_local=local_casa.id, ativo=False))
    db_session.commit()

    resposta = client.get("/api/materiais", headers=_auth_header(usuario_legado))

    assert resposta.json()["total"] == 0


def test_listar_traz_ativo_nulo(client, db_session, usuario_legado, local_casa):
    """`ativo` é opcional no legado (DEFAULT NULL) — não deve ser tratado
    como inativo."""
    material = Material(descricao="Sem status", situacao="Disponível", id_local=local_casa.id)
    material.ativo = None
    db_session.add(material)
    db_session.commit()

    resposta = client.get("/api/materiais", headers=_auth_header(usuario_legado))

    assert resposta.json()["total"] == 1


def test_criar_e_buscar_material(client, usuario_legado, local_casa):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Muletas", "situacao": "Disponível", "id_local": local_casa.id},
        headers=headers,
    )
    assert resposta.status_code == 201
    material_id = resposta.json()["id"]

    resposta = client.get(f"/api/materiais/{material_id}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Muletas"


def test_inativar_material(client, usuario_legado, local_casa):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Cama hospitalar", "situacao": "Disponível", "id_local": local_casa.id},
        headers=headers,
    )
    material_id = resposta.json()["id"]

    resposta = client.delete(f"/api/materiais/{material_id}", headers=headers)
    assert resposta.status_code == 204

    resposta = client.get("/api/materiais", headers=headers)
    assert resposta.json()["total"] == 0


def test_buscar_material_inexistente(client, usuario_legado):
    resposta = client.get("/api/materiais/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_alocar_material(client, db_session, usuario_legado, local_casa):
    from app.features.materiais_locais.models import MaterialLocal

    bazar = MaterialLocal(nome="Bazar")
    db_session.add(bazar)
    db_session.commit()
    db_session.refresh(bazar)

    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Andador", "situacao": "Disponível", "id_local": local_casa.id},
        headers=headers,
    )
    material_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/materiais/{material_id}/alocar", json={"id_local": bazar.id}, headers=headers
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "Alocado"
    assert corpo["id_local"] == bazar.id
    assert corpo["disponivel_emprestimo"] is False


def test_alocar_material_inutilizado_e_rejeitado(client, usuario_legado, local_casa):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Cadeira", "situacao": "Disponível", "id_local": local_casa.id},
        headers=headers,
    )
    material_id = resposta.json()["id"]
    client.post(f"/api/materiais/{material_id}/inutilizar", json={}, headers=headers)

    resposta = client.post(
        f"/api/materiais/{material_id}/alocar", json={"id_local": local_casa.id}, headers=headers
    )

    assert resposta.status_code == 400


def test_alocar_material_local_inexistente(client, usuario_legado, local_casa):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Andador", "situacao": "Disponível", "id_local": local_casa.id},
        headers=headers,
    )
    material_id = resposta.json()["id"]

    resposta = client.post(f"/api/materiais/{material_id}/alocar", json={"id_local": 999}, headers=headers)

    assert resposta.status_code == 404
