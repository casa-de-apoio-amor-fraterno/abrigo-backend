"""Base reutilizável para gerar PDFs de documentos formais (contratos de
estadia, de empréstimo, futuramente outros) usando fpdf2.

Por quê fpdf2: puro Python, sem dependência de biblioteca nativa (testado —
WeasyPrint precisa de GTK/Pango/Cairo instalados no sistema, o que falha de
cara em Windows sem esses pacotes; fpdf2 não tem esse problema e roda igual
em qualquer SO/ambiente de deploy).

Uso típico:

    pdf = DocumentoPDF()
    pdf.titulo_documento("Contrato de Estadia nº 42")
    pdf.paragrafo("Texto do contrato, justificado automaticamente...")
    pdf.campo_assinatura("Assinatura do responsável")
    conteudo: bytes = pdf.gerar_bytes()
"""

import io
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

NOME_ENTIDADE = "CASA DE APOIO AMOR FRATERNO"
NOME_ENTIDADE_TITULO = "Casa de Apoio Amor Fraterno"
SUBTITULO_ENTIDADE = "Associação Família Zalewski"

# Logo real da entidade (recebido 2026-09-16, ver Contrato modelo cedido
# pela CAAF) — vive dentro do pacote da aplicação (não em `C:\repos\caaf\`,
# que é só a raiz do workspace local) pra ser embarcado no deploy.
_CAMINHO_LOGO = Path(__file__).parent / "assets" / "logo-caaf.png"
_ALTURA_LOGO = 16
_LARGURA_LOGO = 32  # reserva à esquerda do cabeçalho — cobre a largura real da imagem (~27mm a 16mm de altura) com folga

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
    def __init__(self, rodape: list[str] | None = None, orientation: str = "P") -> None:
        # `orientation="L"` (paisagem) usado pelos relatórios de listagem
        # (Pessoas, Estadias, Materiais, Empréstimos — ver
        # `app/features/relatorios/service.py`), que têm mais colunas do que
        # cabem em retrato; o contrato continua em retrato (padrão).
        super().__init__(orientation=orientation, format="A4")
        self._rodape = rodape
        self.set_auto_page_break(auto=True, margin=25)
        self.add_page()

    def header(self) -> None:
        # Timbre da entidade (logo + nome), repetido em toda página — o
        # título do documento em si é impresso uma única vez, ver
        # `titulo_documento`, porque no modelo real cedido pela CAAF ele só
        # aparece no topo da primeira página, não em todas.
        # Logo (só o ícone, sem o nome por extenso embutido na imagem —
        # ver `assets/logo-caaf.png`) reservando uma faixa própria à
        # esquerda; o nome da entidade é sempre desenhado à parte, a partir
        # de `_LARGURA_LOGO`, pra nunca sobrepor a imagem.
        y_inicial = self.t_margin
        if _CAMINHO_LOGO.exists():
            self.image(str(_CAMINHO_LOGO), x=self.l_margin, y=y_inicial, h=_ALTURA_LOGO)

        x_texto = self.l_margin + _LARGURA_LOGO
        largura_texto = self.epw - _LARGURA_LOGO
        self.set_xy(x_texto, y_inicial + 1)
        self.set_font("Helvetica", "B", 13)
        self.cell(largura_texto, 6, _texto_seguro(NOME_ENTIDADE), align="C")
        self.set_xy(x_texto, y_inicial + 8)
        self.set_font("Helvetica", "", 10)
        self.cell(largura_texto, 6, _texto_seguro(SUBTITULO_ENTIDADE), align="C")

        y_linha = y_inicial + 20
        self.line(self.l_margin, y_linha, self.w - self.r_margin, y_linha)
        self.set_y(y_linha + 4)

    def footer(self) -> None:
        self.set_y(-20)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(-17)
        self.set_font("Helvetica", "", 7)
        linhas = self._rodape or [f"Página {self.page_no()}"]
        for linha in linhas:
            self.cell(0, 3.5, _texto_seguro(linha), align="C", new_x="LMARGIN", new_y="NEXT")

    def titulo_documento(self, texto: str) -> None:
        """Título impresso uma única vez, no ponto em que é chamado (em
        geral logo após criar o documento) — diferente do timbre do
        cabeçalho, que se repete em toda página."""
        self.set_font("Helvetica", "B", 12)
        self.multi_cell(0, 6, _texto_seguro(texto), align="C")
        self.ln(3)

    def paragrafo(self, texto: str) -> None:
        """Parágrafo justificado. Suporta negrito em **trecho** (sintaxe
        markdown do fpdf2) pra destacar termos-chave do contrato (ex.:
        `**COMODANTE**`, `**30 DIAS**`) igual ao modelo real da CAAF."""
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6, _texto_seguro(texto), align="J", markdown=True)
        self.ln(3)

    def tabela(self, cabecalho: list[str], linhas: list[list[str]]) -> None:
        largura_total = self.epw
        larguras = [largura_total * 0.7, largura_total * 0.3]

        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(230, 230, 230)
        for texto, largura in zip(cabecalho, larguras, strict=True):
            self.cell(largura, 7, _texto_seguro(texto), border=1, align="C", fill=True)
        self.ln()

        self.set_font("Helvetica", "", 10)
        for linha in linhas:
            for texto, largura in zip(linha, larguras, strict=True):
                self.cell(largura, 7, _texto_seguro(texto), border=1, align="C")
            self.ln()
        self.ln(3)

    def tabela_relatorio(
        self, cabecalho: list[str], linhas: list[list[str]], larguras: list[float] | None = None
    ) -> None:
        """Tabela de listagem com número arbitrário de colunas, quebra de
        texto automática e cabeçalho repetido em toda página — usa o suporte
        nativo do fpdf2 (`Table`), diferente de `tabela` acima, que é fixa em
        2 colunas (item/valor) pro corpo do contrato."""
        self.set_font("Helvetica", "", 8)
        with self.table(
            col_widths=larguras,
            text_align="LEFT",
            headings_style=FontFace(emphasis="BOLD", fill_color=(230, 230, 230)),
        ) as tabela:
            linha_cabecalho = tabela.row()
            for texto in cabecalho:
                linha_cabecalho.cell(_texto_seguro(texto))
            for linha in linhas:
                linha_tabela = tabela.row()
                for texto in linha:
                    linha_tabela.cell(_texto_seguro(str(texto)))

    def campo_assinatura(self, rotulo: str, imagem_assinatura: bytes | None = None) -> None:
        """Linha de assinatura. Se `imagem_assinatura` for passado (PNG
        capturado do canvas de assinatura por toque/caneta — ver
        `shared/ui/assinatura-canvas` no frontend), desenha o traço colado
        em cima da linha em vez de deixar em branco pra assinar à caneta no
        papel impresso."""
        largura_linha = 100
        x_inicial = (self.w - largura_linha) / 2

        if imagem_assinatura is not None:
            # Mais espaço que o campo em branco (assinatura feita na tela
            # do celular/tablet — ver `shared/ui/assinatura-canvas` — fica
            # apertada com pouca folga acima/abaixo do traço).
            altura_imagem = 26
            self.ln(8)
            self.image(io.BytesIO(imagem_assinatura), x=x_inicial, w=largura_linha, h=altura_imagem)
            self.ln(3)
        else:
            self.ln(15)

        self.set_x(x_inicial)
        self.cell(largura_linha, 0, border="T")
        self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, _texto_seguro(rotulo), align="C", new_x="LMARGIN", new_y="NEXT")

    def assinaturas_lado_a_lado(self, assinantes: list[tuple[str, str]]) -> None:
        """Duas (ou mais) assinaturas em colunas lado a lado, sem imagem —
        pra assinatura manual no papel impresso (representantes da própria
        entidade, ex.: presidente e gerente geral)."""
        largura_coluna = self.epw / len(assinantes)

        self.ln(15)
        y_linha = self.get_y()
        for indice in range(len(assinantes)):
            x_inicial = self.l_margin + indice * largura_coluna + largura_coluna * 0.15
            self.line(x_inicial, y_linha, x_inicial + largura_coluna * 0.7, y_linha)
        self.set_y(y_linha + 2)

        self.set_font("Helvetica", "B", 10)
        for nome, _ in assinantes:
            self.cell(largura_coluna, 5, _texto_seguro(nome), align="C")
        self.ln()

        self.set_font("Helvetica", "", 9)
        for _, cargo in assinantes:
            self.cell(largura_coluna, 5, _texto_seguro(cargo), align="C")
        self.ln()
        for _ in assinantes:
            self.cell(largura_coluna, 5, _texto_seguro(NOME_ENTIDADE_TITULO), align="C")
        self.ln()

    def gerar_bytes(self) -> bytes:
        return bytes(self.output())
