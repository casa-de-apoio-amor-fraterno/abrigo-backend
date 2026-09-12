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
