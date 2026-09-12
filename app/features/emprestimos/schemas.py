from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class EmprestimoBase(BaseModel):
    id_pessoa: int
    id_usuario: int
    situacao: str
    numero_contrato: str | None = None
    observacao: str | None = None


class EmprestimoItemBase(BaseModel):
    id_material: int
    data_emprestimo: date | None = None
    data_devolucao: date | None = None
    situacao: str | None = None
    renovacao: str | None = None


class EmprestimoItemCreate(EmprestimoItemBase):
    # Quem registrou a inclusão/edição — usado só para gravar
    # `EmprestimoHistorico` (ver service.py); mesmo padrão de
    # `Estadia.id_usuario`, não é um dado do item em si.
    id_usuario: int


class EmprestimoItemUpdate(EmprestimoItemCreate):
    pass


class EmprestimoItemResponse(EmprestimoItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_emprestimo: int
    # Gravada automaticamente pelo backend quando `situacao` vira
    # "Devolvido" (ver service.py) — não é aceita como input do cliente,
    # ao contrário de `data_devolucao` (prevista, digitada manualmente).
    data_devolucao_efetiva: date | None


class EmprestimoCreate(EmprestimoBase):
    # Itens aninhados: o empréstimo ainda não existe pra usar o sub-recurso
    # próprio (POST /emprestimos/{id}/itens), então o front manda os itens
    # junto na criação e o service grava tudo numa transação só (mesmo
    # padrão de `PessoaCreate.composicao_familiar`).
    itens: list[EmprestimoItemCreate] = []


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


class EmprestimoHistoricoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_emprestimo: int
    id_usuario: int
    tipo: str
    observacao: str
    data_cadastro: datetime
