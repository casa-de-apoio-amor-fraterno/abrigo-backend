from datetime import date

from pydantic import BaseModel, ConfigDict

from app.features.composicao_familiar.schemas import ComposicaoFamiliarCreate


class PessoaBase(BaseModel):
    nome: str
    data_nascimento: date
    rg: str | None = None
    cpf: str | None = None
    profissao: str | None = None
    cartao_sus: str | None = None
    endereco: str | None = None
    ponto_referencia: str | None = None
    id_hospital: int | None = None
    id_municipio: int | None = None
    id_estado: int | None = None
    observacao: str | None = None


class PessoaContatoBase(BaseModel):
    numero: str
    nome_contato: str | None = None
    observacao: str | None = None
    principal: bool = False


class PessoaContatoCreate(PessoaContatoBase):
    pass


class PessoaContatoUpdate(PessoaContatoBase):
    pass


class PessoaContatoResponse(PessoaContatoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int


class PessoaCreate(PessoaBase):
    # Composição familiar aninhada: a pessoa ainda não existe pra usar o
    # sub-recurso próprio (POST /pessoas/{id}/composicao-familiar), então o
    # front manda os membros junto na criação e o service grava tudo numa
    # transação só. Mesma trava de perfil do sub-recurso é checada no
    # router (ver `exigir_perfil` em composicao_familiar) — não dá pra
    # confiar só em esconder a aba no front.
    composicao_familiar: list[ComposicaoFamiliarCreate] = []
    # Contatos aninhados: mesmo motivo acima — POST /pessoas/{id}/contatos
    # exige uma pessoa já existente, então os telefones digitados na
    # criação são mandados junto e gravados na mesma transação.
    contatos: list[PessoaContatoCreate] = []


class PessoaUpdate(PessoaBase):
    pass


class PessoaResumoResponse(BaseModel):
    """Shape enxuto usado na listagem/consulta — sem os campos mais pesados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str | None
    telefone_principal: str | None
    data_nascimento: date
    tem_foto: bool


class PessoaResponse(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    data_cadastro: date | None
    tem_foto: bool
    telefone_principal: str | None
