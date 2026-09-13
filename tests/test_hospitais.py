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


def test_criar_hospital(client):
    resposta = client.post("/api/hospitais", json={"nome": "Hospital Novo"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Hospital Novo"
    assert corpo["ativo"] is True


def test_atualizar_hospital(client, db_session):
    hospital = Hospital(nome="Nome Antigo", ativo=True)
    db_session.add(hospital)
    db_session.commit()
    db_session.refresh(hospital)

    resposta = client.put(f"/api/hospitais/{hospital.id}", json={"nome": "Nome Corrigido"})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Nome Corrigido"


def test_atualizar_hospital_inexistente(client):
    resposta = client.put("/api/hospitais/999", json={"nome": "X"})

    assert resposta.status_code == 404


def test_inativar_hospital(client, db_session):
    hospital = Hospital(nome="Hospital a inativar", ativo=True)
    db_session.add(hospital)
    db_session.commit()
    db_session.refresh(hospital)

    resposta = client.delete(f"/api/hospitais/{hospital.id}")

    assert resposta.status_code == 204
    db_session.refresh(hospital)
    assert hospital.ativo is False


def test_inativar_hospital_inexistente(client):
    resposta = client.delete("/api/hospitais/999")

    assert resposta.status_code == 404
