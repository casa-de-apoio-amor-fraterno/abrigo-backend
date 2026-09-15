from app.core.security import criar_token_acesso
from app.features.hospitais.models import Hospital


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_exige_login(client):
    resposta = client.get("/api/hospitais")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/hospitais", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_nao_traz_inativo_por_padrao(client, db_session, usuario_legado):
    db_session.add_all(
        [
            Hospital(nome="Hospital Regional São Camilo", ativo=True),
            Hospital(nome="Hospital Antigo", ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/hospitais", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Hospital Regional São Camilo"


def test_listar_todos_com_apenas_ativos_false(client, db_session, usuario_legado):
    db_session.add_all(
        [
            Hospital(nome="Hospital Regional São Camilo", ativo=True),
            Hospital(nome="Hospital Antigo", ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/hospitais", params={"apenas_ativos": False}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_buscar_hospital_inexistente(client, usuario_legado):
    resposta = client.get("/api/hospitais/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_criar_hospital(client, usuario_legado):
    resposta = client.post(
        "/api/hospitais", json={"nome": "Hospital Novo"}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Hospital Novo"
    assert corpo["ativo"] is True


def test_atualizar_hospital(client, db_session, usuario_legado):
    hospital = Hospital(nome="Nome Antigo", ativo=True)
    db_session.add(hospital)
    db_session.commit()
    db_session.refresh(hospital)

    resposta = client.put(
        f"/api/hospitais/{hospital.id}",
        json={"nome": "Nome Corrigido"},
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Nome Corrigido"


def test_atualizar_hospital_inexistente(client, usuario_legado):
    resposta = client.put(
        "/api/hospitais/999", json={"nome": "X"}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 404


def test_inativar_hospital(client, db_session, usuario_legado):
    hospital = Hospital(nome="Hospital a inativar", ativo=True)
    db_session.add(hospital)
    db_session.commit()
    db_session.refresh(hospital)

    resposta = client.delete(
        f"/api/hospitais/{hospital.id}", headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 204
    db_session.refresh(hospital)
    assert hospital.ativo is False


def test_inativar_hospital_inexistente(client, usuario_legado):
    resposta = client.delete("/api/hospitais/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404
