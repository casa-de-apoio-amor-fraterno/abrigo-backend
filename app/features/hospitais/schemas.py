from pydantic import BaseModel, ConfigDict


class HospitalBase(BaseModel):
    nome: str


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(HospitalBase):
    pass


class HospitalResponse(HospitalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
