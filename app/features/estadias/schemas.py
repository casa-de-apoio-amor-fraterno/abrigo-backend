from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.estadias.models import SituacaoEstadia, TipoPessoaEstadia, UnidadeTempoEstadia


class EstadiaBase(BaseModel):
    id_pessoa: int
    id_quarto: int
    id_usuario: int
    data_entrada: datetime
    data_saida: datetime | None = None
    tempo_estadia: str | None = Field(
        default=None,
        deprecated="Legado, somente leitura. Use tempo_estadia_valor + tempo_estadia_unidade.",
    )
    tempo_estadia_valor: int | None = None
    tempo_estadia_unidade: UnidadeTempoEstadia | None = None
    tipo_pessoa: TipoPessoaEstadia = TipoPessoaEstadia.PACIENTE
    situacao: SituacaoEstadia
    observacao: str | None = None


class EstadiaAcompanhanteBase(BaseModel):
    id_pessoa: int
    data_entrada: datetime
    data_saida: datetime | None = None
    grau_parentesco: str | None = None


class EstadiaAcompanhanteCreate(EstadiaAcompanhanteBase):
    pass


class EstadiaAcompanhanteResponse(EstadiaAcompanhanteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_estadia: int


class EstadiaCreate(EstadiaBase):
    # Acompanhantes aninhados: a estadia ainda não existe pra usar o
    # sub-recurso próprio (POST /estadias/{id}/acompanhantes), então o
    # front manda os acompanhantes junto na criação e o service grava tudo
    # numa transação só (mesmo padrão de `PessoaCreate.composicao_familiar`).
    acompanhantes: list[EstadiaAcompanhanteCreate] = []


class EstadiaUpdate(EstadiaBase):
    pass


class EstadiaEncerrarRequest(BaseModel):
    data_saida: datetime | None = None


class EstadiaResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int
    id_quarto: int
    data_entrada: datetime
    data_saida: datetime | None
    situacao: SituacaoEstadia
    tipo_pessoa: TipoPessoaEstadia


class EstadiaResponse(EstadiaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool | None
