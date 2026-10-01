from datetime import datetime, timedelta

from sqlalchemy import select

from app.features.emprestimos.models import EmprestimoContrato, EmprestimoLinkAssinatura
from tests.test_emprestimo_contrato import _assinatura_base64, _auth_header, _criar_emprestimo

CPF_FINAL = "3344"


def _gerar_link(client, emprestimo, usuario) -> dict:
    resposta = client.post(f"/api/emprestimos/{emprestimo.id}/links-assinatura", headers=_auth_header(usuario))
    assert resposta.status_code == 201
    return resposta.json()


def test_gerar_link_exige_login(client, db_session):
    emprestimo, _ = _criar_emprestimo(db_session)

    assert client.post(f"/api/emprestimos/{emprestimo.id}/links-assinatura").status_code == 401


def test_fluxo_completo_sem_login(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    token = _gerar_link(client, emprestimo, usuario)["token"]

    # Sem login: situação do link, resumo (após CPF), prévia e assinatura.
    assert client.get(f"/api/assinatura/{token}").json()["valido"] is True
    resumo = client.post(f"/api/assinatura/{token}/verificar", json={"cpf_final": CPF_FINAL})
    assert resumo.status_code == 200
    assert resumo.json()["nome_pessoa"] == "Maria da Silva"
    previa = client.post(f"/api/assinatura/{token}/previa", json={"cpf_final": "3344"})
    assert previa.status_code == 200
    assert previa.content.startswith(b"%PDF")

    resposta = client.post(
        f"/api/assinatura/{token}/assinar", json={"cpf_final": CPF_FINAL, "assinatura_png_base64": _assinatura_base64()}
    )
    assert resposta.status_code == 201

    db_session.expire_all()
    contrato = db_session.scalars(select(EmprestimoContrato)).one()
    assert contrato.tipo == "Comodato"
    assert contrato.id_usuario == usuario.id

    # Uso único: o mesmo link não serve de novo.
    assert client.get(f"/api/assinatura/{token}").status_code == 410


def test_cpf_errado_conta_tentativa_e_trava(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    token = _gerar_link(client, emprestimo, usuario)["token"]

    for _ in range(5):
        resposta = client.post(f"/api/assinatura/{token}/verificar", json={"cpf_final": "0000"})
        assert resposta.status_code == 403
        assert "nome_pessoa" not in resposta.text

    # Travado: nem o CPF certo funciona mais.
    certo = client.post(f"/api/assinatura/{token}/verificar", json={"cpf_final": CPF_FINAL})
    assert certo.status_code == 410


def test_link_inexistente_retorna_410(client):
    assert client.get("/api/assinatura/token-que-nao-existe").status_code == 410


def test_link_expirado_retorna_410(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    token = _gerar_link(client, emprestimo, usuario)["token"]
    link = db_session.scalars(select(EmprestimoLinkAssinatura)).one()
    link.expira_em = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    assert client.get(f"/api/assinatura/{token}").status_code == 410


def test_novo_link_revoga_o_anterior(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    antigo = _gerar_link(client, emprestimo, usuario)["token"]
    novo = _gerar_link(client, emprestimo, usuario)["token"]

    assert client.get(f"/api/assinatura/{antigo}").status_code == 410
    assert client.get(f"/api/assinatura/{novo}").status_code == 200
    ativos = client.get(f"/api/emprestimos/{emprestimo.id}/links-assinatura", headers=_auth_header(usuario))
    assert len(ativos.json()) == 1


def test_revogar_link(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    link = _gerar_link(client, emprestimo, usuario)

    resposta = client.delete(
        f"/api/emprestimos/{emprestimo.id}/links-assinatura/{link['id']}", headers=_auth_header(usuario)
    )

    assert resposta.status_code == 204
    assert client.get(f"/api/assinatura/{link['token']}").status_code == 410


def test_nao_gera_link_se_contrato_ja_assinado(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
        headers=_auth_header(usuario),
    )

    resposta = client.post(f"/api/emprestimos/{emprestimo.id}/links-assinatura", headers=_auth_header(usuario))

    assert resposta.status_code == 409


def test_nao_gera_link_para_pessoa_sem_cpf(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    from app.features.pessoas.models import Pessoa

    db_session.get(Pessoa, emprestimo.id_pessoa).cpf = None
    db_session.commit()

    resposta = client.post(f"/api/emprestimos/{emprestimo.id}/links-assinatura", headers=_auth_header(usuario))

    assert resposta.status_code == 422


def test_token_nao_fica_guardado_em_texto_claro(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    token = _gerar_link(client, emprestimo, usuario)["token"]

    link = db_session.scalars(select(EmprestimoLinkAssinatura)).one()

    assert token not in (link.token_hash,)
    assert len(link.token_hash) == 64


def test_codigo_curto_vale_no_lugar_do_token(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    resposta = client.post(f"/api/emprestimos/{emprestimo.id}/links-assinatura", headers=_auth_header(usuario))
    codigo = resposta.json()["codigo"]
    assert len(codigo) == 9 and codigo[4] == "-"

    # Digitado em minúsculas, sem hífen: tudo normalizado.
    digitado = codigo.replace("-", "").lower()
    assert client.get(f"/api/assinatura/{digitado}").status_code == 200
    resumo = client.post(f"/api/assinatura/{codigo}/verificar", json={"cpf_final": CPF_FINAL})
    assert resumo.status_code == 200
    assert resumo.json()["nome_pessoa"] == "Maria da Silva"


def test_cpf_final_precisa_ter_4_digitos(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    token = _gerar_link(client, emprestimo, usuario)["token"]

    assert client.post(f"/api/assinatura/{token}/verificar", json={"cpf_final": "33"}).status_code == 422
    assert client.post(f"/api/assinatura/{token}/verificar", json={"cpf_final": "abcd"}).status_code == 422


def test_chute_de_codigo_inexistente_e_freado_por_ip(client):
    from app.core import rate_limit

    rate_limit._falhas.clear()
    for _ in range(5):
        assert client.get("/api/assinatura/ZZZZ-ZZZZ").status_code == 410

    assert client.get("/api/assinatura/ZZZZ-ZZZZ").status_code == 429
    rate_limit._falhas.clear()
