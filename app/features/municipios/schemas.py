from pydantic import BaseModel, ConfigDict


class MunicipioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    id_estado: int
