from datetime import date, datetime

from app.core.security import criar_token_acesso
from app.features.estadias.models import Estadia, SituacaoEstadia
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.usuarios.models import Usuario


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


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


def test_listar_exige_login(client):
    resposta = client.get("/api/estadias")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/estadias", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_criar_e_buscar_estadia(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    resposta = client.post(
        "/api/estadias",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-10T00:00:00",
            "situacao": "Em acompanhamento",
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["tipo_pessoa"] == "Paciente"
    estadia_id = corpo["id"]

    resposta = client.get(f"/api/estadias/{estadia_id}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Em acompanhamento"


def test_criar_estadia_com_acompanhantes_aninhados(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        headers=headers,
    )
    assert resposta.status_code == 201
    estadia_id = resposta.json()["id"]

    resposta = client.get(f"/api/estadias/{estadia_id}/acompanhantes", headers=headers)
    assert resposta.status_code == 200
    acompanhantes = resposta.json()
    assert len(acompanhantes) == 1
    assert acompanhantes[0]["id_pessoa"] == acompanhante.id
    assert acompanhantes[0]["grau_parentesco"] == "Filho"


def test_listar_filtrado_por_pessoa_acompanhante(client, db_session):
    # Busca global: achar a estadia onde a pessoa aparece como
    # `EstadiaAcompanhante`, não como titular do leito (`Estadia.id_pessoa`).
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        headers=headers,
    )
    estadia_id = resposta.json()["id"]

    resposta = client.get(
        "/api/estadias", params={"id_pessoa_acompanhante": acompanhante.id}, headers=headers
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["id"] == estadia_id

    # A própria pessoa titular não deve aparecer pra esse filtro.
    resposta = client.get(
        "/api/estadias", params={"id_pessoa_acompanhante": deps["pessoa"].id}, headers=headers
    )
    assert resposta.json()["total"] == 0


def test_listar_filtrado_por_situacao(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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

    resposta = client.get("/api/estadias", params={"situacao": "Finalizada"}, headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["situacao"] == "Finalizada"


def test_encerrar_estadia(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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

    resposta = client.post(f"/api/estadias/{estadia.id}/encerrar", headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "Finalizada"
    assert corpo["ativo"] is False


def test_encerrar_estadia_com_tempo_calculado(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        f"/api/estadias/{estadia.id}/encerrar",
        json={
            "data_saida": "2026-01-04T00:00:00",
            "tempo_estadia_valor": 3,
            "tempo_estadia_unidade": "dias",
        },
        headers=headers,
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["tempo_estadia_valor"] == 3
    assert corpo["tempo_estadia_unidade"] == "dias"


def test_adicionar_e_listar_acompanhante(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        headers=headers,
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/estadias/{estadia.id}/acompanhantes", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["grau_parentesco"] == "irmã"


def test_buscar_estadia_inexistente(client, usuario_legado):
    resposta = client.get("/api/estadias/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_acompanhantes_de_estadia_inexistente(client, usuario_legado):
    resposta = client.get("/api/estadias/999/acompanhantes", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_criar_estadia_registra_historico_de_inclusao(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    resposta = client.post(
        "/api/estadias",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-10T00:00:00",
            "situacao": "Em acompanhamento",
        },
        headers=headers,
    )
    estadia_id = resposta.json()["id"]

    resposta = client.get(f"/api/estadias/{estadia_id}/historico", headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["tipo"] == "Inclusão"
    assert corpo[0]["id_usuario"] == deps["usuario"].id


def test_atualizar_estadia_registra_historico_de_alteracao(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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

    resposta = client.put(
        f"/api/estadias/{estadia.id}",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-01T00:00:00",
            "situacao": "Aguardando retorno",
        },
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/estadias/{estadia.id}/historico", headers=headers)
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["tipo"] == "Alteração"
    # Enum precisa aparecer pelo `.value` ("Aguardando retorno"), não pelo
    # nome da instância Python ("SituacaoEstadia.AGUARDANDO_RETORNO").
    assert "Situação: Em acompanhamento -> Aguardando retorno" in corpo[0]["observacao"]


def test_atualizar_estadia_sem_mudanca_nao_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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

    resposta = client.put(
        f"/api/estadias/{estadia.id}",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_quarto": deps["quarto"].id,
            "id_usuario": deps["usuario"].id,
            "data_entrada": "2026-01-01T00:00:00",
            "situacao": "Em acompanhamento",
        },
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/estadias/{estadia.id}/historico", headers=headers)
    assert resposta.json() == []


def test_encerrar_estadia_com_id_usuario_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        f"/api/estadias/{estadia.id}/encerrar",
        json={"id_usuario": deps["usuario"].id},
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/estadias/{estadia.id}/historico", headers=headers)
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["tipo"] == "Encerramento"


def test_encerrar_estadia_sem_id_usuario_nao_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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

    resposta = client.post(f"/api/estadias/{estadia.id}/encerrar", headers=headers)
    assert resposta.status_code == 200

    resposta = client.get(f"/api/estadias/{estadia.id}/historico", headers=headers)
    assert resposta.json() == []


def test_historico_de_estadia_inexistente(client, usuario_legado):
    resposta = client.get("/api/estadias/999/historico", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404
