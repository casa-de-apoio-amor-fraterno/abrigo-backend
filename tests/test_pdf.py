import io

from PIL import Image

from app.shared.pdf import DocumentoPDF


def _png_1x1() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="black").save(buffer, format="PNG")
    return buffer.getvalue()


def test_documento_pdf_gera_bytes_de_um_pdf_valido():
    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato de Estadia nº 1")
    pdf.paragrafo(
        "Texto de exemplo do contrato, longo o suficiente pra quebrar em "
        "mais de uma linha e testar o alinhamento justificado do parágrafo."
    )
    pdf.campo_assinatura("Assinatura do responsável")

    conteudo = pdf.gerar_bytes()

    assert isinstance(conteudo, bytes)
    assert conteudo.startswith(b"%PDF-")
    assert conteudo.rstrip().endswith(b"%%EOF")
    assert len(conteudo) > 500


def test_documento_pdf_nao_quebra_com_pontuacao_tipografica():
    """Travessão, aspas curvas etc. não existem em Latin-1 (fonte core) —
    a geração não pode falhar por causa disso (ex.: texto colado do Word)."""
    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato — versão de teste")
    pdf.paragrafo("Texto com travessão — aspas “curvas” e reticências… um teste.")
    pdf.campo_assinatura("Assinatura — testemunha")

    conteudo = pdf.gerar_bytes()

    assert conteudo.startswith(b"%PDF-")


def test_campo_assinatura_com_imagem_gera_pdf_valido():
    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato com assinatura desenhada")
    pdf.paragrafo("Texto do contrato antes da assinatura.")
    pdf.campo_assinatura("Assinatura do paciente", imagem_assinatura=_png_1x1())

    conteudo = pdf.gerar_bytes()

    assert conteudo.startswith(b"%PDF-")
    assert len(conteudo) > 500


def test_documento_pdf_quebra_pagina_com_texto_longo():
    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato de Empréstimo nº 1")
    for _ in range(200):
        pdf.paragrafo("Linha de teste pra forçar quebra de página automática. " * 3)

    conteudo = pdf.gerar_bytes()

    assert pdf.page_no() > 1
    assert conteudo.startswith(b"%PDF-")


def test_tabela_e_assinaturas_lado_a_lado_geram_pdf_valido():
    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato com tabela de valores")
    pdf.paragrafo("Texto antes da tabela.")
    pdf.tabela(
        ["Item", "Valor"],
        [["Cadeira de Rodas", "R$ 150,00"], ["Andador", "R$ 50,00"]],
    )
    pdf.assinaturas_lado_a_lado([("Fulana", "Presidente"), ("Beltrana", "Gerente Geral")])

    conteudo = pdf.gerar_bytes()

    assert conteudo.startswith(b"%PDF-")
    assert len(conteudo) > 500
