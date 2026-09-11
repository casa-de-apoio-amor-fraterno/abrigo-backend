from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComposicaoFamiliar(Base):
    """Mapeia a tabela `composicao_familiar` (schema confirmado no dump de
    produção `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Sub-rotina de `Pessoa`, mesma regra de acesso restrito de
    `avaliacao_social` (ver `composicao_familiar.legacy.md`).

    `idade` é `varchar(60)`, não `int` — dado real pode ter valores como
    "5 meses", não só anos completos; mantido como `String`.
    """

    __tablename__ = "composicao_familiar"

    id: Mapped[int] = mapped_column("id_composicao_familiar", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    nome: Mapped[str] = mapped_column(String(60))
    idade: Mapped[str | None] = mapped_column(String(60), nullable=True)
    grau_parentesco: Mapped[str] = mapped_column(String(60))
    estado_civil: Mapped[str | None] = mapped_column(String(60), nullable=True)
    renda: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ocupacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
