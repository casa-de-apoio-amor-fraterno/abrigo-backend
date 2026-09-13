"""Base reutilizável para gerar PDFs de documentos formais (contratos de
estadia, de empréstimo, futuramente outros) usando fpdf2.

Por quê fpdf2: puro Python, sem dependência de biblioteca nativa (testado —
WeasyPrint precisa de GTK/Pango/Cairo instalados no sistema, o que falha de
cara em Windows sem esses pacotes; fpdf2 não tem esse problema e roda igual
em qualquer SO/ambiente de deploy).

Uso típico:

    pdf = DocumentoPDF(titulo="Contrato de Estadia nº 42")
    pdf.paragrafo("Texto do contrato, justificado automaticamente...")
    pdf.campo_assinatura("Assinatura do responsável")
    conteudo: bytes = pdf.gerar_bytes()
"""

from fpdf import FPDF

NOME_ENTIDADE = "Casa de Apoio Amor Fraterno"

# A fonte core (Helvetica) só suporta Latin-1 — cobre acentuação do
# português normalmente (á, ã, ç, º...), mas não pontuação "tipográfica"
# fora dessa faixa (travessão, aspas curvas, reticências como um único
# caractere). Sem embutir uma fonte TrueType Unicode (nenhuma disponível
# livre pra redistribuir de forma simples no ambiente deste projeto —
# Arial é proprietária, DejaVu não está disponível via pip aqui),
# normalizamos essas variantes pra equivalentes em Latin-1 antes de
# desenhar o texto, com um fallback final que nunca deixa a geração do PDF
# quebrar por causa de um caractere inesperado (ex.: colado do Word).
_SUBSTITUICOES_TIPOGRAFICAS = {
    "—": "-",
    "–": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "…": "...",
}


def _texto_seguro(texto: str) -> str:
    for original, substituto in _SUBSTITUICOES_TIPOGRAFICAS.items():
        texto = texto.replace(original, substituto)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


class DocumentoPDF(FPDF):
    def __init__(self, titulo: str) -> None:
        super().__init__(format="A4")
        self._titulo = titulo
        self.set_auto_page_break(auto=True, margin=25)
        self.add_page()

    def header(self) -> None:
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, _texto_seguro(NOME_ENTIDADE), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, _texto_seguro(self._titulo), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def paragrafo(self, texto: str) -> None:
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, _texto_seguro(texto), align="J")
        self.ln(3)

    def campo_assinatura(self, rotulo: str) -> None:
        self.ln(15)
        largura_linha = 100
        x_inicial = (self.w - largura_linha) / 2
        self.set_x(x_inicial)
        self.cell(largura_linha, 0, border="T")
        self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, _texto_seguro(rotulo), align="C", new_x="LMARGIN", new_y="NEXT")

    def gerar_bytes(self) -> bytes:
        return bytes(self.output())
