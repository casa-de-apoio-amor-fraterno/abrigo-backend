from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Situação de empréstimo/item: combo fechado no legado (constantes de
# `CasaApoio.Material.Constants.pas`, reaproveitadas por Emprestimo apesar
# do nome da unit) — só 3 estados reais, tanto no item (`rgpSituacao`,
# `dscItemEmprestimo`) quanto no cabeçalho.
#
# `Emprestimo.situacao` (cabeçalho) **não é digitada pelo usuário** — no
# legado o campo é `TcxDBTextEdit` com `Enabled = False`, e é recalculada
# automaticamente por `AtualizarSituacaoEmprestimo`
# (untFrmManutencaoEmprestimo.pas) toda vez que um item é salvo, com
# prioridade Renovado > Pendente > Devolvido (qualquer item Renovado vence;
# senão qualquer item Pendente vence; só vira Devolvido se todos os itens
# estiverem Devolvido; sem itens, default Pendente). Ver
# `_recalcular_situacao` em service.py.
SituacaoEmprestimo = Literal["Pendente", "Renovado", "Devolvido"]


class EmprestimoBase(BaseModel):
    id_pessoa: int
    id_usuario: int
    numero_contrato: str | None = None
    observacao: str | None = None


class EmprestimoItemBase(BaseModel):
    id_material: int
    data_emprestimo: date | None = None
    data_devolucao: date | None = None
    situacao: SituacaoEmprestimo | None = None
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


class EmprestimoDevolverRequest(BaseModel):
    # Quem registrou a devolução — usado só para gravar
    # `EmprestimoHistorico` (mesmo padrão de `EmprestimoItemCreate.id_usuario`).
    id_usuario: int
    data_devolucao: date | None = None


class EmprestimoResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int
    situacao: SituacaoEmprestimo
    numero_contrato: str | None


class EmprestimoResponse(EmprestimoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    situacao: SituacaoEmprestimo
    ativo: bool


class EmprestimoHistoricoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_emprestimo: int
    id_usuario: int
    tipo: str
    observacao: str
    data_cadastro: datetime
