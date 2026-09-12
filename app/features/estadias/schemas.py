from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.features.estadias.models import SituacaoEstadia, TipoPessoaEstadia


class EstadiaBase(BaseModel):
    id_pessoa: int
    id_quarto: int
    id_usuario: int
    data_entrada: datetime
    data_saida: datetime | None = None
    tempo_estadia: str | None = None
    tipo_pessoa: TipoPessoaEstadia = TipoPessoaEstadia.PACIENTE
    situacao: SituacaoEstadia
    observacao: str | None = None


class EstadiaCreate(EstadiaBase):
    pass


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
