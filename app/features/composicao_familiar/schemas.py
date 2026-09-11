from pydantic import BaseModel, ConfigDict


class ComposicaoFamiliarBase(BaseModel):
    nome: str
    idade: str | None = None
    grau_parentesco: str
    estado_civil: str | None = None
    renda: str | None = None
    ocupacao: str | None = None


class ComposicaoFamiliarCreate(ComposicaoFamiliarBase):
    pass


class ComposicaoFamiliarUpdate(ComposicaoFamiliarBase):
    pass


class ComposicaoFamiliarResponse(ComposicaoFamiliarBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int
