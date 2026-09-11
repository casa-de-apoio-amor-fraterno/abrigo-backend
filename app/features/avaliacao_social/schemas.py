from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvaliacaoSocialBase(BaseModel):
    fumante: bool | None = None
    residencia: str | None = None
    energia_eletrica: bool | None = None
    agua_encanada: bool | None = None
    tipo_construcao: str | None = None
    renda_mensal_familiar: str | None = None
    quantas_pessoas_contribuem_formacao_renda: str | None = None
    alguem_recebe_beneficio_previdenciario_governo: str | None = None
    diagnostico: str | None = None
    tratamento_realizado: str | None = None
    casos_cancer_familia: str | None = None
    necessita_medicamento_uso_continuo: bool | None = None
    medicamento_disponibilizado_sus: bool | None = None
    custo_mensal_medicamento: str | None = None
    alimentacao_especifica: str | None = None
    equipamento_para_locomocao: str | None = None
    data_movimento: datetime | None = None


class AvaliacaoSocialCreate(AvaliacaoSocialBase):
    pass


class AvaliacaoSocialUpdate(AvaliacaoSocialBase):
    pass


class AvaliacaoSocialResponse(AvaliacaoSocialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_pessoa: int
