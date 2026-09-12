from datetime import date

from pydantic import BaseModel, ConfigDict


class VoluntarioBase(BaseModel):
    nome: str
    setor: str | None = None
    data_nascimento: date | None = None
    estado_civil: str | None = None
    cpf: str | None = None
    endereco: str | None = None
    formacao: str | None = None
    observacao: str | None = None


class VoluntarioContatoBase(BaseModel):
    numero: str
    nome_contato: str | None = None
    observacao: str | None = None
    principal: bool = False


class VoluntarioContatoCreate(VoluntarioContatoBase):
    pass


class VoluntarioContatoUpdate(VoluntarioContatoBase):
    pass


class VoluntarioContatoResponse(VoluntarioContatoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_voluntario: int


class VoluntarioCreate(VoluntarioBase):
    # Contatos aninhados: o voluntário ainda não existe pra usar o
    # sub-recurso próprio (POST /voluntarios/{id}/contatos), então o front
    # manda os telefones junto na criação e o service grava tudo numa
    # transação só (mesmo padrão de `PessoaCreate.contatos`).
    contatos: list[VoluntarioContatoCreate] = []


class VoluntarioUpdate(VoluntarioBase):
    pass


class VoluntarioResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone_principal: str | None
    setor: str | None


class VoluntarioResponse(VoluntarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    telefone_principal: str | None
