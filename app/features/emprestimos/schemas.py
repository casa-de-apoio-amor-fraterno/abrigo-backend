from datetime import date

from pydantic import BaseModel, ConfigDict


class EmprestimoBase(BaseModel):
    id_pessoa: int
    id_usuario: int
    situacao: str
    numero_contrato: str | None = None
    observacao: str | None = None


class EmprestimoCreate(EmprestimoBase):
    pass


class EmprestimoUpdate(EmprestimoBase):
    pass


class EmprestimoResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int
    situacao: str
    numero_contrato: str | None


class EmprestimoResponse(EmprestimoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool


class EmprestimoItemBase(BaseModel):
    id_material: int
    data_emprestimo: date | None = None
    data_devolucao: date | None = None
    situacao: str | None = None
    renovacao: str | None = None


class EmprestimoItemCreate(EmprestimoItemBase):
    pass


class EmprestimoItemUpdate(EmprestimoItemBase):
    pass


class EmprestimoItemResponse(EmprestimoItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_emprestimo: int
