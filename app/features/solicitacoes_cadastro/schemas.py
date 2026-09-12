from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.features.solicitacoes_cadastro.models import SituacaoSolicitacaoCadastro


class SolicitacaoCadastroResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str | None
    telefone: str | None
    data_nascimento: date
    situacao: SituacaoSolicitacaoCadastro
    data_solicitacao: datetime
    tem_foto: bool


class SolicitacaoCadastroResponse(SolicitacaoCadastroResumoResponse):
    id_pessoa: int | None
    id_usuario_analise: int | None
    data_analise: datetime | None
