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
            "data_nascimento": "1995-03-20",
        },
    )
    assert resposta.status_code == 201
    pessoa_id = resposta.json()["id"]

    resposta = client.get(f"/api/pessoas/{pessoa_id}")
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Paula"
    assert resposta.json()["telefone_principal"] is None


def test_contatos_de_pessoa(client):
    pessoa_id = client.post(
        "/api/pessoas", json={"nome": "Beatriz", "data_nascimento": "1980-01-01"}
    ).json()["id"]

    resposta = client.post(
        f"/api/pessoas/{pessoa_id}/contatos",
        json={"numero": "47988132030", "nome_contato": "Esposa", "principal": True},
    )
    assert resposta.status_code == 201
    contato_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/pessoas/{pessoa_id}/contatos", json={"numero": "111"}
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/pessoas/{pessoa_id}")
    assert resposta.json()["telefone_principal"] == "47988132030"

    resposta = client.get(f"/api/pessoas/{pessoa_id}/contatos")
    assert len(resposta.json()) == 2

    resposta = client.put(
        f"/api/pessoas/{pessoa_id}/contatos/{contato_id}", json={"numero": "222"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["numero"] == "222"

    resposta = client.delete(f"/api/pessoas/{pessoa_id}/contatos/{contato_id}")
    assert resposta.status_code == 204

    resposta = client.get(f"/api/pessoas/{pessoa_id}/contatos")
    assert len(resposta.json()) == 1


def test_contato_de_pessoa_inexistente(client):
    pessoa_id = client.post(
        "/api/pessoas", json={"nome": "Carla", "data_nascimento": "1980-01-01"}
    ).json()["id"]

    resposta = client.put(
        f"/api/pessoas/{pessoa_id}/contatos/999", json={"numero": "111"}
    )
    assert resposta.status_code == 404

    resposta = client.delete(f"/api/pessoas/{pessoa_id}/contatos/999")
    assert resposta.status_code == 404


def test_buscar_pessoa_inexistente(client):
    resposta = client.get("/api/pessoas/999")

    assert resposta.status_code == 404


def _criar_pessoa(client, nome: str = "Foto Teste") -> int:
    resposta = client.post(
        "/api/pessoas",
        json={"nome": nome, "data_nascimento": "1990-01-01"},
    )
    return resposta.json()["id"]


def test_pessoa_sem_foto_tem_tem_foto_falso(client):
    pessoa_id = _criar_pessoa(client)

    resposta = client.get(f"/api/pessoas/{pessoa_id}")

    assert resposta.json()["tem_foto"] is False


def test_obter_foto_inexistente_retorna_404(client):
    pessoa_id = _criar_pessoa(client)

    resposta = client.get(f"/api/pessoas/{pessoa_id}/foto")

    assert resposta.status_code == 404


def test_salvar_e_obter_foto(client):
    pessoa_id = _criar_pessoa(client)
    conteudo = b"conteudo-fake-de-imagem"

    resposta = client.put(
        f"/api/pessoas/{pessoa_id}/foto",
        files={"arquivo": ("foto.jpg", conteudo, "image/jpeg")},
    )
    assert resposta.status_code == 200
    assert resposta.json()["tem_foto"] is True

    resposta = client.get(f"/api/pessoas/{pessoa_id}/foto")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "image/jpeg"
    assert resposta.content == conteudo


def test_salvar_foto_formato_nao_suportado(client):
    pessoa_id = _criar_pessoa(client)

    resposta = client.put(
        f"/api/pessoas/{pessoa_id}/foto",
        files={"arquivo": ("foto.gif", b"abc", "image/gif")},
    )

    assert resposta.status_code == 400


def test_salvar_foto_maior_que_limite(client):
    pessoa_id = _criar_pessoa(client)
    conteudo_grande = b"a" * (5 * 1024 * 1024 + 1)

    resposta = client.put(
        f"/api/pessoas/{pessoa_id}/foto",
        files={"arquivo": ("foto.jpg", conteudo_grande, "image/jpeg")},
    )

    assert resposta.status_code == 400


def test_remover_foto(client):
    pessoa_id = _criar_pessoa(client)
    client.put(
        f"/api/pessoas/{pessoa_id}/foto",
        files={"arquivo": ("foto.jpg", b"conteudo", "image/jpeg")},
    )

    resposta = client.delete(f"/api/pessoas/{pessoa_id}/foto")
    assert resposta.status_code == 204

    resposta = client.get(f"/api/pessoas/{pessoa_id}")
    assert resposta.json()["tem_foto"] is False
