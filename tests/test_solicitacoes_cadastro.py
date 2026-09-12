from datetime import date, datetime

from app.core.security import criar_token_acesso
from app.features.solicitacoes_cadastro.models import SolicitacaoCadastroPaciente


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_criar_solicitacao_nao_exige_login(client):
    # Público — é assim que o paciente se auto-cadastra pelo próprio
    # celular, sem sessão nenhuma (ver login.page + "Sou paciente").
    resposta = client.post(
        "/api/solicitacoes-cadastro",
        data={"nome": "Ana Maria Bona", "data_nascimento": "1990-01-01", "cpf": "12345678900"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["situacao"] == "Pendente"
    assert corpo["id_pessoa"] is None
    assert corpo["tem_foto"] is False


def test_listar_sem_token_retorna_401(client):
    resposta = client.get("/api/solicitacoes-cadastro")

    assert resposta.status_code == 401


def test_listar_com_token_retorna_pendentes(client, usuario_legado):
    client.post(
        "/api/solicitacoes-cadastro",
        data={"nome": "Ana Maria Bona", "data_nascimento": "1990-01-01"},
    )

    resposta = client.get("/api/solicitacoes-cadastro", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["nome"] == "Ana Maria Bona"


def test_aprovar_cria_pessoa_e_marca_situacao(client, db_session, usuario_legado):
    resposta = client.post(
        "/api/solicitacoes-cadastro",
        data={
            "nome": "Ana Maria Bona",
            "data_nascimento": "1990-01-01",
            "cpf": "12345678900",
            "telefone": "(42) 99999-0000",
        },
    )
    solicitacao_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/solicitacoes-cadastro/{solicitacao_id}/aprovar", headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "Aprovada"
    assert corpo["id_pessoa"] is not None
    assert corpo["id_usuario_analise"] == usuario_legado.id

    pessoa = client.get(f"/api/pessoas/{corpo['id_pessoa']}").json()
    assert pessoa["nome"] == "Ana Maria Bona"
    assert pessoa["cpf"] == "12345678900"
    assert pessoa["telefone_principal"] == "(42) 99999-0000"


def test_revogar_nao_cria_pessoa(client, usuario_legado):
    resposta = client.post(
        "/api/solicitacoes-cadastro",
        data={"nome": "Ana Maria Bona", "data_nascimento": "1990-01-01"},
    )
    solicitacao_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/solicitacoes-cadastro/{solicitacao_id}/revogar", headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["situacao"] == "Revogada"
    assert corpo["id_pessoa"] is None


def test_aprovar_solicitacao_ja_analisada_retorna_409(client, usuario_legado):
    resposta = client.post(
        "/api/solicitacoes-cadastro",
        data={"nome": "Ana Maria Bona", "data_nascimento": "1990-01-01"},
    )
    solicitacao_id = resposta.json()["id"]
    client.post(f"/api/solicitacoes-cadastro/{solicitacao_id}/revogar", headers=_auth_header(usuario_legado))

    resposta = client.post(
        f"/api/solicitacoes-cadastro/{solicitacao_id}/aprovar", headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 409


def test_aprovar_solicitacao_inexistente_retorna_404(client, usuario_legado):
    resposta = client.post(
        "/api/solicitacoes-cadastro/999/aprovar", headers=_auth_header(usuario_legado)
    )

    assert resposta.status_code == 404


def test_criar_com_foto_invalida_retorna_400(client):
    resposta = client.post(
        "/api/solicitacoes-cadastro",
        data={"nome": "Ana Maria Bona", "data_nascimento": "1990-01-01"},
        files={"arquivo": ("foto.txt", b"nao e uma imagem", "text/plain")},
    )

    assert resposta.status_code == 400


def test_obter_foto_sem_token_retorna_401(client, db_session):
    solicitacao = SolicitacaoCadastroPaciente(
        nome="Ana Maria Bona",
        data_nascimento=date(1990, 1, 1),
        situacao="Pendente",
        data_solicitacao=datetime(2026, 9, 12),
    )
    db_session.add(solicitacao)
    db_session.commit()
    db_session.refresh(solicitacao)

    resposta = client.get(f"/api/solicitacoes-cadastro/{solicitacao.id}/foto")

    assert resposta.status_code == 401
