from app.features.materiais.models import Material


def test_listar_vazio(client):
    resposta = client.get("/api/materiais")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_descricao(client, db_session):
    db_session.add_all(
        [
            Material(descricao="Cadeira de rodas", situacao="Disponível", local="Casa"),
            Material(descricao="Muletas", situacao="Disponível", local="Casa"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/materiais", params={"busca": "cadeira"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["descricao"] == "Cadeira de rodas"


def test_listar_apenas_disponiveis_emprestimo(client, db_session):
    db_session.add_all(
        [
            Material(
                descricao="Cadeira de rodas",
                situacao="Disponível",
                local="Casa",
                disponivel_emprestimo=True,
            ),
            Material(descricao="Impressora", situacao="Disponível", local="Casa", disponivel_emprestimo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/materiais", params={"apenas_disponiveis_emprestimo": True})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["descricao"] == "Cadeira de rodas"


def test_listar_nao_traz_inativo(client, db_session):
    db_session.add(Material(descricao="Baixado", situacao="Baixado", local="Casa", ativo=False))
    db_session.commit()

    resposta = client.get("/api/materiais")

    assert resposta.json()["total"] == 0


def test_listar_traz_ativo_nulo(client, db_session):
    """`ativo` é opcional no legado (DEFAULT NULL) — não deve ser tratado
    como inativo."""
    material = Material(descricao="Sem status", situacao="Disponível", local="Casa")
    material.ativo = None
    db_session.add(material)
    db_session.commit()

    resposta = client.get("/api/materiais")

    assert resposta.json()["total"] == 1


def test_criar_e_buscar_material(client):
    resposta = client.post(
        "/api/materiais",
        json={"descricao": "Muletas", "situacao": "Disponível", "local": "Casa"},
    )
    assert resposta.status_code == 201
    material_id = resposta.json()["id"]

    resposta = client.get(f"/api/materiais/{material_id}")
    assert resposta.status_code == 200
    assert resposta.json()["descricao"] == "Muletas"


def test_inativar_material(client):
    resposta = client.post(
        "/api/materiais", json={"descricao": "Cama hospitalar", "situacao": "Disponível", "local": "Casa"}
    )
    material_id = resposta.json()["id"]

    resposta = client.delete(f"/api/materiais/{material_id}")
    assert resposta.status_code == 204

    resposta = client.get("/api/materiais")
    assert resposta.json()["total"] == 0


def test_buscar_material_inexistente(client):
    resposta = client.get("/api/materiais/999")

    assert resposta.status_code == 404
