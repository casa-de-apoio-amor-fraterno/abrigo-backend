from typing import Literal

from pydantic import BaseModel, ConfigDict

# Lista fechada de situações do material (antes texto livre — ver
# `models.py`). "Baixado" foi renomeado para "Inutilizado" (nome que o
# time realmente usa) e "Alocado" é novo: material disponibilizado em
# algum lugar do Abrigo ou da CAAF (ex.: Bazar), fora de "Casa", mas ainda
# não emprestado a uma pessoa (que é "Emprestado"). Decisão do time,
# 2026-09-26.
SituacaoMaterial = Literal["Disponível", "Alocado", "Emprestado", "Inutilizado"]


class MaterialBase(BaseModel):
    descricao: str
    numero_patrimonio: str | None = None
    disponivel_emprestimo: bool = False
    situacao: SituacaoMaterial
    id_local: int
    observacao: str | None = None
    motivo_baixa: str | None = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    pass


class MaterialResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    numero_patrimonio: str | None
    situacao: SituacaoMaterial
    disponivel_emprestimo: bool
    tem_foto: bool


class MaterialResponse(MaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool | None
    tem_foto: bool


class MaterialInutilizarRequest(BaseModel):
    motivo_baixa: str | None = None


class MaterialAlocarRequest(BaseModel):
    id_local: int
