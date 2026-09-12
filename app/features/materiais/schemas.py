from pydantic import BaseModel, ConfigDict


class MaterialBase(BaseModel):
    descricao: str
    codigo_identificacao: str | None = None
    disponivel_emprestimo: bool = False
    situacao: str
    local: str
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
    codigo_identificacao: str | None
    situacao: str
    disponivel_emprestimo: bool
    tem_foto: bool


class MaterialResponse(MaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool | None
    tem_foto: bool
