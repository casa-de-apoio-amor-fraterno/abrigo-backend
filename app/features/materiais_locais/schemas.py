from pydantic import BaseModel, ConfigDict


class MaterialLocalBase(BaseModel):
    nome: str


class MaterialLocalCreate(MaterialLocalBase):
    pass


class MaterialLocalUpdate(MaterialLocalBase):
    pass


class MaterialLocalResponse(MaterialLocalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
