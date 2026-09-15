from app.core.security import criar_token_acesso
from app.features.estados.models import Estado


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_exige_login(client):
    resposta = client.get("/api/estados")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/estados", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_ordenado_por_nome(client, db_session, usuario_legado):
    db_session.add_all(
        [
            Estado(id=35, nome="São Paulo", uf="SP"),
            Estado(id=11, nome="Rondônia", uf="RO"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/estados", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    nomes = [e["nome"] for e in resposta.json()]
    assert nomes == ["Rondônia", "São Paulo"]


def test_buscar_estado_existente(client, db_session, usuario_legado):
    db_session.add(Estado(id=53, nome="Distrito Federal", uf="DF"))
    db_session.commit()

    resposta = client.get("/api/estados/53", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json()["uf"] == "DF"


def test_buscar_estado_inexistente(client, usuario_legado):
    resposta = client.get("/api/estados/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404
