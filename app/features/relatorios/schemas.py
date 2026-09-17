import enum

from pydantic import BaseModel


class PeriodoRelatorio(str, enum.Enum):
    """Janela de tempo pra filtrar relatórios que têm um campo de data
    relevante (Pessoas: data de cadastro; Estadias: data de entrada;
    Empréstimos: data do empréstimo) — Materiais não tem campo de data no
    legado, por isso não aceita esse filtro (ver `service.py`)."""

    SEMANAL = "semanal"
    QUINZENAL = "quinzenal"
    MENSAL = "mensal"
    SEMESTRAL = "semestral"
    ANUAL = "anual"


class RelatorioResumoItem(BaseModel):
    rotulo: str
    valor: str


class RelatorioResumoResponse(BaseModel):
    itens: list[RelatorioResumoItem]
