from app.core.security import criar_token_acesso
from app.features.voluntarios.models import Voluntario


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_exige_login(client):
    resposta = client.get("/api/voluntarios")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/voluntarios", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_nome(client, db_session, usuario_legado):
    db_session.add_all(
        [
            Voluntario(nome="Adélio Zbiegniew Rzewuski", cpf="00468703934"),
            Voluntario(nome="Amanda Burmester", cpf="03667609981"),
        ]
    )
    db_session.commit()

    resposta = client.get(
        "/api/voluntarios", params={"busca": "amanda"}, headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Amanda Burmester"


def test_listar_nao_traz_inativo(client, db_session, usuario_legado):
    db_session.add(Voluntario(nome="Inativo", ativo=False))
    db_session.commit()

    resposta = client.get("/api/voluntarios", headers=_auth_header(usuario_legado))

    assert resposta.json()["total"] == 0


def test_criar_e_buscar_voluntario(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/voluntarios",
        json={"nome": "Ana Rita", "setor": "Roupas"},
        headers=headers,
    )
    assert resposta.status_code == 201
    voluntario_id = resposta.json()["id"]

    resposta = client.get(f"/api/voluntarios/{voluntario_id}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Rita"
    assert resposta.json()["telefone_principal"] is None


def test_criar_voluntario_com_contatos_aninhados(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    resposta = client.post(
        "/api/voluntarios",
        json={
            "nome": "Beatriz Nunes",
            "contatos": [
                {"numero": "42999990000", "nome_contato": "Beatriz", "principal": True},
                {"numero": "42988880000"},
            ],
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    voluntario_id = resposta.json()["id"]
    assert resposta.json()["telefone_principal"] == "42999990000"

    resposta = client.get(f"/api/voluntarios/{voluntario_id}/contatos", headers=headers)
    assert resposta.status_code == 200
    contatos = resposta.json()
    assert len(contatos) == 2
    assert {c["numero"] for c in contatos} == {"42999990000", "42988880000"}


def test_atualizar_voluntario(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    resposta = client.post("/api/voluntarios", json={"nome": "Carla"}, headers=headers)
    voluntario_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/voluntarios/{voluntario_id}",
        json={"nome": "Carla Renata", "setor": "Nutrição"},
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carla Renata"
    assert resposta.json()["setor"] == "Nutrição"


def test_inativar_voluntario(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    resposta = client.post("/api/voluntarios", json={"nome": "Cecília"}, headers=headers)
    voluntario_id = resposta.json()["id"]

    resposta = client.delete(f"/api/voluntarios/{voluntario_id}", headers=headers)
    assert resposta.status_code == 204

    resposta = client.get("/api/voluntarios", headers=headers)
    assert resposta.json()["total"] == 0


def test_buscar_voluntario_inexistente(client, usuario_legado):
    resposta = client.get("/api/voluntarios/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_adicionar_contato_e_ver_telefone_principal(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    voluntario_id = client.post("/api/voluntarios", json={"nome": "Dora"}, headers=headers).json()["id"]

    resposta = client.post(
        f"/api/voluntarios/{voluntario_id}/contatos",
        json={"numero": "47988132030", "principal": True},
        headers=headers,
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/voluntarios/{voluntario_id}", headers=headers)
    assert resposta.json()["telefone_principal"] == "47988132030"

    resposta = client.get("/api/voluntarios", headers=headers)
    item = next(i for i in resposta.json()["items"] if i["id"] == voluntario_id)
    assert item["telefone_principal"] == "47988132030"


def test_atualizar_e_remover_contato(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    voluntario_id = client.post("/api/voluntarios", json={"nome": "Elza"}, headers=headers).json()["id"]
    contato_id = client.post(
        f"/api/voluntarios/{voluntario_id}/contatos", json={"numero": "111"}, headers=headers
    ).json()["id"]

    resposta = client.put(
        f"/api/voluntarios/{voluntario_id}/contatos/{contato_id}",
        json={"numero": "222", "nome_contato": "Recado com a vizinha"},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert resposta.json()["numero"] == "222"

    resposta = client.delete(
        f"/api/voluntarios/{voluntario_id}/contatos/{contato_id}", headers=headers
    )
    assert resposta.status_code == 204

    resposta = client.get(f"/api/voluntarios/{voluntario_id}/contatos", headers=headers)
    assert resposta.json() == []
