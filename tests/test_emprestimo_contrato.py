import base64
import io
from datetime import date

from PIL import Image

from app.core.security import criar_token_acesso
from app.features.emprestimos.models import Emprestimo
from app.features.materiais.models import Material
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario


def _auth_header(usuario: Usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def _assinatura_base64() -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="black").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def _criar_emprestimo(db_session) -> tuple[Emprestimo, Usuario]:
    pessoa = Pessoa(nome="Maria da Silva", cpf="11122233344", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    usuario = Usuario(login="joana", nome="Joana Assistente", perfil="Geral", senha="123456")
    material = Material(descricao="Cadeira de rodas", situacao="Disponível", local="Casa", disponivel_emprestimo=True)
    db_session.add_all([pessoa, usuario, material])
    db_session.commit()
    db_session.refresh(pessoa)
    db_session.refresh(usuario)
    db_session.refresh(material)

    emprestimo = Emprestimo(id_pessoa=pessoa.id, id_usuario=usuario.id, situacao="Pendente")
    db_session.add(emprestimo)
    db_session.commit()
    db_session.refresh(emprestimo)
    return emprestimo, usuario


def test_assinar_contrato_exige_login(client, db_session):
    emprestimo, _ = _criar_emprestimo(db_session)

    resposta = client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
    )

    assert resposta.status_code == 401


def test_assinar_contrato_gera_pdf(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)

    resposta = client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
        headers=_auth_header(usuario),
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id_emprestimo"] == emprestimo.id
    assert corpo["id_usuario"] == usuario.id

    resposta = client.get(f"/api/emprestimos/{emprestimo.id}/contrato", headers=_auth_header(usuario))
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo.id}/contrato/pdf", headers=_auth_header(usuario))
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/pdf"
    assert resposta.content.startswith(b"%PDF-")


def test_assinar_contrato_ja_assinado_retorna_409(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)
    headers = _auth_header(usuario)

    client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
        headers=headers,
    )
    resposta = client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
        headers=headers,
    )

    assert resposta.status_code == 409


def test_assinar_contrato_base64_invalido_retorna_400(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)

    resposta = client.post(
        f"/api/emprestimos/{emprestimo.id}/contrato",
        json={"assinatura_png_base64": "não é base64 válido!!!"},
        headers=_auth_header(usuario),
    )

    assert resposta.status_code == 400


def test_contrato_de_emprestimo_inexistente_retorna_404(client, db_session):
    pessoa = Pessoa(nome="Ana", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    usuario = Usuario(login="carlos", nome="Carlos", perfil="Geral", senha="123456")
    db_session.add_all([pessoa, usuario])
    db_session.commit()
    db_session.refresh(usuario)

    resposta = client.get("/api/emprestimos/999/contrato", headers=_auth_header(usuario))
    assert resposta.status_code == 404

    resposta = client.post(
        "/api/emprestimos/999/contrato",
        json={"assinatura_png_base64": _assinatura_base64()},
        headers=_auth_header(usuario),
    )
    assert resposta.status_code == 404


def test_buscar_contrato_antes_de_assinar_retorna_404(client, db_session):
    emprestimo, usuario = _criar_emprestimo(db_session)

    resposta = client.get(f"/api/emprestimos/{emprestimo.id}/contrato", headers=_auth_header(usuario))

    assert resposta.status_code == 404
