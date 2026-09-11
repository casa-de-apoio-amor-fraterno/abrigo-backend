from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AvaliacaoSocial(Base):
    """Mapeia a tabela `avaliacao_social` (schema confirmado no dump de
    produção `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Dados sensíveis (renda, diagnóstico médico, benefícios sociais) — só
    acessível a `Usuario.perfil == 'Assistente Social'` (valor real gravado
    pelo legado, verificado no dump de produção — não é o snake_case usado
    inicialmente), regra nova (o legado não restringia acesso por perfil).
    Ver `avaliacao_social.legacy.md`.

    `casos_cancer_familia` é `text` no legado, não `varchar(3)` como os
    outros campos Sim/Não desta tabela — mantido como `String`, não
    convertido pra boolean (o tipo da coluna já indica que pode conter mais
    que só Sim/Não, mesmo que os dados de amostra sejam só isso).
    """

    __tablename__ = "avaliacao_social"

    id: Mapped[int] = mapped_column("id_avaliacao_social", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    fumante: Mapped[bool | None] = mapped_column(nullable=True)
    residencia: Mapped[str | None] = mapped_column(String(10), nullable=True)
    energia_eletrica: Mapped[bool | None] = mapped_column(nullable=True)
    agua_encanada: Mapped[bool | None] = mapped_column(nullable=True)
    tipo_construcao: Mapped[str | None] = mapped_column(String(10), nullable=True)
    renda_mensal_familiar: Mapped[str | None] = mapped_column(String(60), nullable=True)
    quantas_pessoas_contribuem_formacao_renda: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
    alguem_recebe_beneficio_previdenciario_governo: Mapped[str | None] = mapped_column(
        String(60), nullable=True
    )
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    tratamento_realizado: Mapped[str | None] = mapped_column(Text, nullable=True)
    casos_cancer_familia: Mapped[str | None] = mapped_column(Text, nullable=True)
    necessita_medicamento_uso_continuo: Mapped[bool | None] = mapped_column(nullable=True)
    medicamento_disponibilizado_sus: Mapped[bool | None] = mapped_column(nullable=True)
    custo_mensal_medicamento: Mapped[str | None] = mapped_column(String(60), nullable=True)
    alimentacao_especifica: Mapped[str | None] = mapped_column(Text, nullable=True)
    equipamento_para_locomocao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_movimento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
