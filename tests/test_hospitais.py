from app.features.hospitais.models import Hospital


def test_listar_vazio(client):
    resposta = client.get("/api/hospitais")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_nao_traz_inativo_por_padrao(client, db_session):
    db_session.add_all(
        [
            Hospital(nome="Hospital Regional São Camilo", ativo=True),
            Hospital(nome="Hospital Antigo", ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/hospitais")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["nome"] == "Hospital Regional São Camilo"


def test_listar_todos_com_apenas_ativos_false(client, db_session):
    db_session.add_all(
        [
            Hospital(nome="Hospital Regional São Camilo", ativo=True),
            Hospital(nome="Hospital Antigo", ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/hospitais", params={"apenas_ativos": False})

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_buscar_hospital_inexistente(client):
    resposta = client.get("/api/hospitais/999")

    assert resposta.status_code == 404
