from pydantic import BaseModel, ConfigDict


class EstadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    uf: str
