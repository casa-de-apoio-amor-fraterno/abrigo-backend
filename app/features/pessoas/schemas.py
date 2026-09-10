from datetime import date

from pydantic import BaseModel, ConfigDict


class PessoaBase(BaseModel):
    nome: str
    data_nascimento: date
    rg: str | None = None
    cpf: str | None = None
    profissao: str | None = None
    cartao_sus: str | None = None
    endereco: str | None = None
    ponto_referencia: str | None = None
    telefone: str | None = None
    id_hospital: int | None = None
    id_municipio: int | None = None
    id_estado: int | None = None
    observacao: str | None = None


class PessoaCreate(PessoaBase):
    pass


class PessoaUpdate(PessoaBase):
    pass


class PessoaResumoResponse(BaseModel):
    """Shape enxuto usado na listagem/consulta — sem os campos mais pesados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str | None
    telefone: str | None
    data_nascimento: date


class PessoaResponse(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    data_cadastro: date
