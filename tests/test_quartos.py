from app.features.quartos.models import Quarto


def test_listar_vazio(client):
    resposta = client.get("/api/quartos")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_listar_nao_traz_inativo_por_padrao(client, db_session):
    db_session.add_all(
        [
            Quarto(numero="11", leito=4, ativo=True),
            Quarto(numero="99", leito=0, ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/quartos")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["numero"] == "11"


def test_listar_todos_com_apenas_ativos_false(client, db_session):
    db_session.add_all(
        [
            Quarto(numero="11", leito=4, ativo=True),
            Quarto(numero="99", leito=0, ativo=False),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/quartos", params={"apenas_ativos": False})

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_criar_e_buscar_quarto(client):
    resposta = client.post(
        "/api/quartos",
        json={"descricao": "Cadeirante", "numero": "16", "leito": 2},
    )
    assert resposta.status_code == 201
    quarto_id = resposta.json()["id"]

    resposta = client.get(f"/api/quartos/{quarto_id}")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["numero"] == "16"
    assert corpo["leito"] == 2
    assert corpo["ativo"] is True


def test_atualizar_quarto(client):
    resposta = client.post("/api/quartos", json={"numero": "20", "leito": 2})
    quarto_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/quartos/{quarto_id}",
        json={"descricao": "Reformado", "numero": "20", "leito": 3},
    )

    assert resposta.status_code == 200
    assert resposta.json()["leito"] == 3
    assert resposta.json()["descricao"] == "Reformado"


def test_inativar_quarto(client):
    resposta = client.post("/api/quartos", json={"numero": "21", "leito": 2})
    quarto_id = resposta.json()["id"]

    resposta = client.delete(f"/api/quartos/{quarto_id}")
    assert resposta.status_code == 204

    resposta = client.get("/api/quartos")
    assert resposta.json() == []


def test_buscar_quarto_inexistente(client):
    resposta = client.get("/api/quartos/999")

    assert resposta.status_code == 404


def test_atualizar_quarto_inexistente(client):
    resposta = client.put("/api/quartos/999", json={"numero": "1", "leito": 1})

    assert resposta.status_code == 404


def test_criar_quarto_rejeita_leito_nao_numerico(client):
    resposta = client.post("/api/quartos", json={"numero": "22", "leito": "2 leitos"})

    assert resposta.status_code == 422
