from datetime import date

from pydantic import BaseModel, ConfigDict


class VoluntarioBase(BaseModel):
    nome: str
    telefone: str
    setor: str | None = None
    data_nascimento: date | None = None
    estado_civil: str | None = None
    cpf: str | None = None
    endereco: str | None = None
    formacao: str | None = None
    observacao: str | None = None


class VoluntarioCreate(VoluntarioBase):
    pass


class VoluntarioUpdate(VoluntarioBase):
    pass


class VoluntarioResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: str
    setor: str | None


class VoluntarioResponse(VoluntarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
