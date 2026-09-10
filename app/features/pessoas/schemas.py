from pydantic import BaseModel, ConfigDict


class PessoaBase(BaseModel):
    nome: str
    cpf: str | None = None
    telefone: str | None = None


class PessoaCreate(PessoaBase):
    pass


class PessoaUpdate(PessoaBase):
    pass


class PessoaResponse(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
