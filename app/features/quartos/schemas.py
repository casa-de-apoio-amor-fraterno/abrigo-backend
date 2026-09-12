from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuartoBase(BaseModel):
    descricao: str | None = None
    numero: str
    leito: int


class QuartoCreate(QuartoBase):
    pass


class QuartoUpdate(QuartoBase):
    pass


class QuartoResponse(QuartoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool


class QuartoOcupanteResponse(BaseModel):
    id_estadia: int
    id_pessoa: int
    nome_pessoa: str
    data_entrada: datetime


class QuartoOcupacaoResponse(BaseModel):
    """Painel de ocupação (tela Início).

    Achado 2026-09-12: dado real tem estadias 'Em acompanhamento' nunca
    fechadas no legado (ex.: um quarto de 4 leitos com 39 estadias nessa
    situação, algumas de 2018) — não dá pra confiar em "situação !=
    Finalizada" pra saber quem está no quarto agora. Heurística adotada:
    `ocupantes` são só as `leito` estadias 'Em acompanhamento' mais
    recentes (por `data_entrada`) de cada quarto; qualquer excedente vira
    `pendentes_revisao` — provavelmente esquecido sem finalizar, fica
    visível pra equipe decidir (finalizar manualmente), sem forçar isso
    automaticamente. Ver `service.listar_ocupacao`.
    """

    id: int
    numero: str
    descricao: str | None
    leito: int
    ocupantes: list[QuartoOcupanteResponse]
    pendentes_revisao: list[QuartoOcupanteResponse]
