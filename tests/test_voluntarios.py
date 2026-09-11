from app.features.voluntarios.models import Voluntario


def test_listar_vazio(client):
    resposta = client.get("/api/voluntarios")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_nome(client, db_session):
    db_session.add_all(
        [
            Voluntario(nome="Adélio Zbiegniew Rzewuski", telefone="42999751020", cpf="00468703934"),
            Voluntario(nome="Amanda Burmester", telefone="4299975579", cpf="03667609981"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/voluntarios", params={"busca": "amanda"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Amanda Burmester"


def test_listar_nao_traz_inativo(client, db_session):
    db_session.add(Voluntario(nome="Inativo", telefone="999999999", ativo=False))
    db_session.commit()

    resposta = client.get("/api/voluntarios")

    assert resposta.json()["total"] == 0


def test_criar_e_buscar_voluntario(client):
    resposta = client.post(
        "/api/voluntarios",
        json={"nome": "Ana Rita", "telefone": "988132030", "setor": "Roupas"},
    )
    assert resposta.status_code == 201
    voluntario_id = resposta.json()["id"]

    resposta = client.get(f"/api/voluntarios/{voluntario_id}")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Rita"


def test_atualizar_voluntario(client):
    resposta = client.post("/api/voluntarios", json={"nome": "Carla", "telefone": "999500588"})
    voluntario_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/voluntarios/{voluntario_id}",
        json={"nome": "Carla Renata", "telefone": "999500588", "setor": "Nutrição"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carla Renata"
    assert resposta.json()["setor"] == "Nutrição"


def test_inativar_voluntario(client):
    resposta = client.post("/api/voluntarios", json={"nome": "Cecília", "telefone": "988354713"})
    voluntario_id = resposta.json()["id"]

    resposta = client.delete(f"/api/voluntarios/{voluntario_id}")
    assert resposta.status_code == 204

    resposta = client.get("/api/voluntarios")
    assert resposta.json()["total"] == 0


def test_buscar_voluntario_inexistente(client):
    resposta = client.get("/api/voluntarios/999")

    assert resposta.status_code == 404
