from datetime import date

from app.features.pessoas.models import Pessoa


def test_listar_vazio(client):
    resposta = client.get("/api/pessoas")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_listar_com_busca_por_nome(client, db_session):
    db_session.add_all(
        [
            Pessoa(
                nome="Maria da Silva",
                cpf="11111111111",
                data_nascimento=date(1990, 1, 1),
                data_cadastro=date.today(),
            ),
            Pessoa(
                nome="João Souza",
                cpf="22222222222",
                data_nascimento=date(1985, 5, 5),
                data_cadastro=date.today(),
            ),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/pessoas", params={"busca": "maria"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Maria da Silva"


def test_listar_nao_traz_pessoa_inativa(client, db_session):
    db_session.add(
        Pessoa(
            nome="Pessoa Inativa",
            data_nascimento=date(1990, 1, 1),
            data_cadastro=date.today(),
            ativo=False,
        )
    )
    db_session.commit()

    resposta = client.get("/api/pessoas")

    assert resposta.json()["total"] == 0


def test_listar_com_busca_por_cpf(client, db_session):
    db_session.add_all(
        [
            Pessoa(
                nome="Maria da Silva",
                cpf="11111111111",
                data_nascimento=date(1990, 1, 1),
                data_cadastro=date.today(),
            ),
            Pessoa(
                nome="João Souza",
                cpf="22222222222",
                data_nascimento=date(1985, 5, 5),
                data_cadastro=date.today(),
            ),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/pessoas", params={"busca": "2222"})

    assert resposta.status_code == 200
    assert resposta.json()["total"] == 1


def test_criar_e_buscar_pessoa(client):
    resposta = client.post(
        "/api/pessoas",
        json={
            "nome": "Ana Paula",
            "cpf": "33333333333",
            "telefone": "11999999999",
            "data_nascimento": "1995-03-20",
        },
    )
    assert resposta.status_code == 201
    pessoa_id = resposta.json()["id"]

    resposta = client.get(f"/api/pessoas/{pessoa_id}")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Paula"


def test_buscar_pessoa_inexistente(client):
    resposta = client.get("/api/pessoas/999")

    assert resposta.status_code == 404
