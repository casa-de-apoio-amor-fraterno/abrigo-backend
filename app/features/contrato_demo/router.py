"""Protótipo pra validar o fluxo "assinar contrato no tablet" — capturar a
assinatura por toque/caneta no canvas do frontend (ver `shared/ui/assinatura-
canvas` no Angular) e colar num PDF gerado no backend.

Não é a feature de contrato de verdade (essa depende do texto/cláusulas e do
vínculo com `Estadia`/`Emprestimo`, ainda não definidos) — só prova que o
fluxo end-to-end funciona. Substituir por `contratos_estadia`/
`contratos_emprestimo` quando o conteúdo real for definido.
"""

from base64 import b64decode
from binascii import Error as Base64Error

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.features.auth.dependencies import usuario_atual
from app.shared.pdf import DocumentoPDF

router = APIRouter()


class ContratoDemoRequest(BaseModel):
    nome_pessoa: str = Field(min_length=1)
    texto_contrato: str = Field(min_length=1)
    # PNG do canvas de assinatura, em base64 — aceita tanto a string crua
    # quanto uma data URL completa ("data:image/png;base64,...."), que é o
    # que `HTMLCanvasElement.toDataURL()` produz no frontend.
    assinatura_png_base64: str = Field(min_length=1)


@router.post("/gerar-pdf", dependencies=[Depends(usuario_atual)])
def gerar_pdf(dados: ContratoDemoRequest) -> Response:
    base64_puro = dados.assinatura_png_base64.split(",")[-1]
    try:
        imagem_assinatura = b64decode(base64_puro, validate=True)
    except (Base64Error, ValueError) as exc:
        # ValueError: caracteres fora de ASCII (b64decode não aceita nem
        # tenta antes de validar o alfabeto base64) — Base64Error: alfabeto
        # base64 válido só em ASCII, mas padding/conteúdo incorretos.
        raise HTTPException(status_code=400, detail="Assinatura em base64 inválida") from exc

    pdf = DocumentoPDF()
    pdf.titulo_documento(f"Contrato (protótipo) - {dados.nome_pessoa}")
    pdf.paragrafo(dados.texto_contrato)
    pdf.campo_assinatura(f"Assinatura de {dados.nome_pessoa}", imagem_assinatura)

    return Response(content=pdf.gerar_bytes(), media_type="application/pdf")
