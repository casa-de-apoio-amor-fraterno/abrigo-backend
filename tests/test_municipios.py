from app.core.security import criar_token_acesso
from app.features.estados.models import Estado
from app.features.municipios.models import Municipio


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_exige_login(client):
    resposta = client.get("/api/municipios")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/municipios", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_filtrado_por_estado(client, db_session, usuario_legado):
    db_session.add_all(
        [
            Estado(id=11, nome="Rondônia", uf="RO"),
            Estado(id=35, nome="São Paulo", uf="SP"),
        ]
    )
    db_session.commit()
    db_session.add_all(
        [
            Municipio(id=1100015, nome="Alta Floresta DOeste", id_estado=11),
            Municipio(id=3550308, nome="São Paulo", id_estado=35),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/municipios", params={"id_estado": 11}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Alta Floresta DOeste"


def test_listar_com_busca_por_nome(client, db_session, usuario_legado):
    db_session.add(Estado(id=11, nome="Rondônia", uf="RO"))
    db_session.commit()
    db_session.add_all(
        [
            Municipio(id=1100015, nome="Alta Floresta DOeste", id_estado=11),
            Municipio(id=1100023, nome="Ariquemes", id_estado=11),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/municipios", params={"busca": "ariq"}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Ariquemes"


def test_buscar_municipio_inexistente(client, usuario_legado):
    resposta = client.get("/api/municipios/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404
