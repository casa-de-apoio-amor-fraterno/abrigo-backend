from datetime import date, datetime

from app.features.estadias.models import Estadia, SituacaoEstadia
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.usuarios.models import Usuario


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


def test_listar_ocupacao(client, db_session):
    # Quarto de 1 leito com 3 estadias "Em acompanhamento" — cenário real
    # (achado 2026-09-12): só a mais recente conta como ocupante, as outras
    # duas (mais antigas, provavelmente esquecidas sem finalizar) viram
    # pendentes_revisao.
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    quarto_com_excedente = Quarto(numero="11", leito=1, ativo=True)
    quarto_vazio = Quarto(numero="12", leito=3, ativo=True)
    quarto_inativo = Quarto(numero="99", leito=1, ativo=False)
    db_session.add_all([pessoa, usuario, quarto_com_excedente, quarto_vazio, quarto_inativo])
    db_session.commit()
    db_session.refresh(pessoa)
    db_session.refresh(usuario)
    db_session.refresh(quarto_com_excedente)

    db_session.add_all(
        [
            Estadia(
                id_pessoa=pessoa.id,
                id_quarto=quarto_com_excedente.id,
                id_usuario=usuario.id,
                data_entrada=datetime(2018, 11, 17),
                situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
            ),
            Estadia(
                id_pessoa=pessoa.id,
                id_quarto=quarto_com_excedente.id,
                id_usuario=usuario.id,
                data_entrada=datetime(2020, 3, 1),
                situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
            ),
            Estadia(
                id_pessoa=pessoa.id,
                id_quarto=quarto_com_excedente.id,
                id_usuario=usuario.id,
                data_entrada=datetime(2026, 1, 3),
                situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
            ),
            # Finalizada não conta pra ocupação nem pra pendentes.
            Estadia(
                id_pessoa=pessoa.id,
                id_quarto=quarto_com_excedente.id,
                id_usuario=usuario.id,
                data_entrada=datetime(2026, 1, 4),
                situacao=SituacaoEstadia.FINALIZADA,
            ),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/quartos/ocupacao")

    assert resposta.status_code == 200
    corpo = {q["numero"]: q for q in resposta.json()}
    assert set(corpo.keys()) == {"11", "12"}  # quarto inativo não aparece

    quarto_11 = corpo["11"]
    assert quarto_11["leito"] == 1
    assert len(quarto_11["ocupantes"]) == 1
    assert quarto_11["ocupantes"][0]["data_entrada"] == "2026-01-03T00:00:00"
    assert len(quarto_11["pendentes_revisao"]) == 2

    quarto_12 = corpo["12"]
    assert quarto_12["leito"] == 3
    assert quarto_12["ocupantes"] == []
    assert quarto_12["pendentes_revisao"] == []
