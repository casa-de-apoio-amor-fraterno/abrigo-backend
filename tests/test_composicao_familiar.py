from datetime import date

from app.core.security import criar_token_acesso
from app.features.pessoas.models import Pessoa


def _criar_pessoa(db_session) -> Pessoa:
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    db_session.add(pessoa)
    db_session.commit()
    db_session.refresh(pessoa)
    return pessoa


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_listar_sem_token_retorna_401(client, db_session):
    pessoa = _criar_pessoa(db_session)

    resposta = client.get(f"/api/pessoas/{pessoa.id}/composicao-familiar")

    assert resposta.status_code == 401


def test_listar_com_perfil_errado_retorna_403(client, db_session, usuario_migrado):
    pessoa = _criar_pessoa(db_session)

    resposta = client.get(
        f"/api/pessoas/{pessoa.id}/composicao-familiar", headers=_auth_header(usuario_migrado)
    )

    assert resposta.status_code == 403


def test_criar_listar_e_remover_membro(client, db_session, usuario_legado):
    pessoa = _criar_pessoa(db_session)

    resposta = client.post(
        f"/api/pessoas/{pessoa.id}/composicao-familiar",
        json={"nome": "Josiane", "grau_parentesco": "Filha", "idade": "5 meses"},
        headers=_auth_header(usuario_legado),
    )
    assert resposta.status_code == 201
    membro_id = resposta.json()["id"]

    resposta = client.get(
        f"/api/pessoas/{pessoa.id}/composicao-familiar", headers=_auth_header(usuario_legado)
    )
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1

    resposta = client.delete(
        f"/api/pessoas/{pessoa.id}/composicao-familiar/{membro_id}",
        headers=_auth_header(usuario_legado),
    )
    assert resposta.status_code == 204

    resposta = client.get(
        f"/api/pessoas/{pessoa.id}/composicao-familiar", headers=_auth_header(usuario_legado)
    )
    assert resposta.json() == []


def test_atualizar_membro(client, db_session, usuario_legado):
    pessoa = _criar_pessoa(db_session)
    resposta = client.post(
        f"/api/pessoas/{pessoa.id}/composicao-familiar",
        json={"nome": "Josiane", "grau_parentesco": "Filha"},
        headers=_auth_header(usuario_legado),
    )
    membro_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/pessoas/{pessoa.id}/composicao-familiar/{membro_id}",
        json={"nome": "Josiane", "grau_parentesco": "Filha", "ocupacao": "Estudante"},
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 200
    assert resposta.json()["ocupacao"] == "Estudante"


def test_remover_membro_de_outra_pessoa_retorna_404(client, db_session, usuario_legado):
    pessoa_1 = _criar_pessoa(db_session)
    pessoa_2 = Pessoa(nome="João Souza", data_nascimento=date(1985, 5, 5), data_cadastro=date.today())
    db_session.add(pessoa_2)
    db_session.commit()
    db_session.refresh(pessoa_2)

    resposta = client.post(
        f"/api/pessoas/{pessoa_1.id}/composicao-familiar",
        json={"nome": "Josiane", "grau_parentesco": "Filha"},
        headers=_auth_header(usuario_legado),
    )
    membro_id = resposta.json()["id"]

    resposta = client.delete(
        f"/api/pessoas/{pessoa_2.id}/composicao-familiar/{membro_id}",
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 404
