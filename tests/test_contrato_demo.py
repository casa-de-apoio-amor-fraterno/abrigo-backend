import base64
import io

from PIL import Image

from app.core.security import criar_token_acesso


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def _assinatura_base64(com_prefixo_data_url: bool = False) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="black").save(buffer, format="PNG")
    codificado = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{codificado}" if com_prefixo_data_url else codificado


def test_gerar_pdf_exige_login(client):
    resposta = client.post(
        "/api/contrato-demo/gerar-pdf",
        json={
            "nome_pessoa": "Maria",
            "texto_contrato": "Texto de teste.",
            "assinatura_png_base64": _assinatura_base64(),
        },
    )
    assert resposta.status_code == 401


def test_gerar_pdf_com_assinatura_retorna_pdf(client, usuario_legado):
    resposta = client.post(
        "/api/contrato-demo/gerar-pdf",
        json={
            "nome_pessoa": "Maria da Silva",
            "texto_contrato": "Texto de teste do contrato de estadia.",
            "assinatura_png_base64": _assinatura_base64(),
        },
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/pdf"
    assert resposta.content.startswith(b"%PDF-")


def test_gerar_pdf_aceita_data_url_completa(client, usuario_legado):
    resposta = client.post(
        "/api/contrato-demo/gerar-pdf",
        json={
            "nome_pessoa": "João",
            "texto_contrato": "Texto de teste.",
            "assinatura_png_base64": _assinatura_base64(com_prefixo_data_url=True),
        },
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 200
    assert resposta.content.startswith(b"%PDF-")


def test_gerar_pdf_com_base64_invalido_retorna_400(client, usuario_legado):
    resposta = client.post(
        "/api/contrato-demo/gerar-pdf",
        json={
            "nome_pessoa": "João",
            "texto_contrato": "Texto de teste.",
            "assinatura_png_base64": "isso não é base64 válido!!!",
        },
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 400
