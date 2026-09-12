from datetime import date, datetime

from app.features.estadias.models import Estadia, SituacaoEstadia
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.usuarios.models import Usuario


def _criar_dependencias(db_session) -> dict:
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    quarto = Quarto(numero="11", leito=4)
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    db_session.add_all([pessoa, quarto, usuario])
    db_session.commit()
    db_session.refresh(pessoa)
    db_session.refresh(quarto)
    db_session.refresh(usuario)
    return {"pessoa": pessoa, "quarto": quarto, "usuario": usuario}


def test_listar_vazio(client):
    resposta = client.get("/api/estadias")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_criar_e_buscar_estadia(client, db_session):
    deps = _criar_dependencias(db_session)

    resposta = client.post(
        "/api/estadias",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-10T00:00:00",
            "situacao": "Em acompanhamento",
        },
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_pessoa"] == "Paciente"
    estadia_id = corpo["id"]

    resposta = client.get(f"/api/estadias/{estadia_id}")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Em acompanhamento"


def test_criar_estadia_com_acompanhantes_aninhados(client, db_session):
    deps = _criar_dependencias(db_session)
    acompanhante = Pessoa(
        nome="José da Silva", data_nascimento=date(1988, 5, 20), data_cadastro=date.today()
    )
    db_session.add(acompanhante)
    db_session.commit()
    db_session.refresh(acompanhante)

    resposta = client.post(
        "/api/estadias",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-10T00:00:00",
            "situacao": "Em acompanhamento",
            "acompanhantes": [
                {
                    "id_pessoa": acompanhante.id,
                    "data_entrada": "2026-01-10T00:00:00",
                    "grau_parentesco": "Filho",
                }
            ],
        },
    )
    assert resposta.status_code == 201
    estadia_id = resposta.json()["id"]

    resposta = client.get(f"/api/estadias/{estadia_id}/acompanhantes")
    assert resposta.status_code == 200
    acompanhantes = resposta.json()
    assert len(acompanhantes) == 1
    assert acompanhantes[0]["id_pessoa"] == acompanhante.id
    assert acompanhantes[0]["grau_parentesco"] == "Filho"


def test_listar_filtrado_por_pessoa_acompanhante(client, db_session):
    # Busca global: achar a estadia onde a pessoa aparece como
    # `EstadiaAcompanhante`, não como titular do leito (`Estadia.id_pessoa`).
    deps = _criar_dependencias(db_session)
    acompanhante = Pessoa(
        nome="José da Silva", data_nascimento=date(1988, 5, 20), data_cadastro=date.today()
    )
    db_session.add(acompanhante)
    db_session.commit()
    db_session.refresh(acompanhante)

    resposta = client.post(
        "/api/estadias",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-10T00:00:00",
            "situacao": "Em acompanhamento",
            "acompanhantes": [
                {
                    "id_pessoa": acompanhante.id,
                    "data_entrada": "2026-01-10T00:00:00",
                    "grau_parentesco": "Filho",
                }
            ],
        },
    )
    estadia_id = resposta.json()["id"]

    resposta = client.get("/api/estadias", params={"id_pessoa_acompanhante": acompanhante.id})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["id"] == estadia_id

    # A própria pessoa titular não deve aparecer pra esse filtro.
    resposta = client.get("/api/estadias", params={"id_pessoa_acompanhante": deps["pessoa"].id})
    assert resposta.json()["total"] == 0


def test_listar_filtrado_por_situacao(client, db_session):
    deps = _criar_dependencias(db_session)
    db_session.add_all(
        [
            Estadia(
                id_pessoa=deps["pessoa"].id,
                id_quarto=deps["quarto"].id,
                id_usuario=deps["usuario"].id,
                data_entrada=datetime(2026, 1, 1),
                situacao=SituacaoEstadia.FINALIZADA,
            ),
            Estadia(
                id_pessoa=deps["pessoa"].id,
                id_quarto=deps["quarto"].id,
                id_usuario=deps["usuario"].id,
                data_entrada=datetime(2026, 2, 1),
                situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
            ),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/estadias", params={"situacao": "Finalizada"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["situacao"] == "Finalizada"


def test_encerrar_estadia(client, db_session):
    deps = _criar_dependencias(db_session)
    estadia = Estadia(
        id_pessoa=deps["pessoa"].id,
        id_quarto=deps["quarto"].id,
        id_usuario=deps["usuario"].id,
        data_entrada=datetime(2026, 1, 1),
        situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
    )
    db_session.add(estadia)
    db_session.commit()
    db_session.refresh(estadia)

    resposta = client.post(f"/api/estadias/{estadia.id}/encerrar")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "Finalizada"
    assert corpo["ativo"] is False


def test_adicionar_e_listar_acompanhante(client, db_session):
    deps = _criar_dependencias(db_session)
    acompanhante = Pessoa(
        nome="João Souza", data_nascimento=date(1985, 5, 5), data_cadastro=date.today()
    )
    db_session.add(acompanhante)
    db_session.commit()
    db_session.refresh(acompanhante)

    estadia = Estadia(
        id_pessoa=deps["pessoa"].id,
        id_quarto=deps["quarto"].id,
        id_usuario=deps["usuario"].id,
        data_entrada=datetime(2026, 1, 1),
        situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
    )
    db_session.add(estadia)
    db_session.commit()
    db_session.refresh(estadia)

    resposta = client.post(
        f"/api/estadias/{estadia.id}/acompanhantes",
        json={
            "id_pessoa": acompanhante.id,
            "data_entrada": "2026-01-01T00:00:00",
            "grau_parentesco": "irmã",
        },
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/estadias/{estadia.id}/acompanhantes")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["grau_parentesco"] == "irmã"


def test_buscar_estadia_inexistente(client):
    resposta = client.get("/api/estadias/999")

    assert resposta.status_code == 404


def test_acompanhantes_de_estadia_inexistente(client):
    resposta = client.get("/api/estadias/999/acompanhantes")

    assert resposta.status_code == 404
