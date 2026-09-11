from app.features.voluntarios.models import Voluntario


def test_listar_vazio(client):
    resposta = client.get("/api/voluntarios")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_nome(client, db_session):
    db_session.add_all(
        [
            Voluntario(nome="Adélio Zbiegniew Rzewuski", cpf="00468703934"),
            Voluntario(nome="Amanda Burmester", cpf="03667609981"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/voluntarios", params={"busca": "amanda"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Amanda Burmester"


def test_listar_nao_traz_inativo(client, db_session):
    db_session.add(Voluntario(nome="Inativo", ativo=False))
    db_session.commit()

    resposta = client.get("/api/voluntarios")

    assert resposta.json()["total"] == 0


def test_criar_e_buscar_voluntario(client):
    resposta = client.post(
        "/api/voluntarios",
        json={"nome": "Ana Rita", "setor": "Roupas"},
    )
    assert resposta.status_code == 201
    voluntario_id = resposta.json()["id"]

    resposta = client.get(f"/api/voluntarios/{voluntario_id}")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Rita"
    assert resposta.json()["telefone_principal"] is None


def test_atualizar_voluntario(client):
    resposta = client.post("/api/voluntarios", json={"nome": "Carla"})
    voluntario_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/voluntarios/{voluntario_id}",
        json={"nome": "Carla Renata", "setor": "Nutrição"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carla Renata"
    assert resposta.json()["setor"] == "Nutrição"


def test_inativar_voluntario(client):
    resposta = client.post("/api/voluntarios", json={"nome": "Cecília"})
    voluntario_id = resposta.json()["id"]

    resposta = client.delete(f"/api/voluntarios/{voluntario_id}")
    assert resposta.status_code == 204

    resposta = client.get("/api/voluntarios")
    assert resposta.json()["total"] == 0


def test_buscar_voluntario_inexistente(client):
    resposta = client.get("/api/voluntarios/999")

    assert resposta.status_code == 404


def test_adicionar_contato_e_ver_telefone_principal(client):
    voluntario_id = client.post("/api/voluntarios", json={"nome": "Dora"}).json()["id"]

    resposta = client.post(
        f"/api/voluntarios/{voluntario_id}/contatos",
        json={"numero": "47988132030", "principal": True},
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/voluntarios/{voluntario_id}")
    assert resposta.json()["telefone_principal"] == "47988132030"

    resposta = client.get("/api/voluntarios")
    item = next(i for i in resposta.json()["items"] if i["id"] == voluntario_id)
    assert item["telefone_principal"] == "47988132030"


def test_atualizar_e_remover_contato(client):
    voluntario_id = client.post("/api/voluntarios", json={"nome": "Elza"}).json()["id"]
    contato_id = client.post(
        f"/api/voluntarios/{voluntario_id}/contatos", json={"numero": "111"}
    ).json()["id"]

    resposta = client.put(
        f"/api/voluntarios/{voluntario_id}/contatos/{contato_id}",
        json={"numero": "222", "nome_contato": "Recado com a vizinha"},
    )
    assert resposta.status_code == 200
    assert resposta.json()["numero"] == "222"

    resposta = client.delete(f"/api/voluntarios/{voluntario_id}/contatos/{contato_id}")
    assert resposta.status_code == 204

    resposta = client.get(f"/api/voluntarios/{voluntario_id}/contatos")
    assert resposta.json() == []
