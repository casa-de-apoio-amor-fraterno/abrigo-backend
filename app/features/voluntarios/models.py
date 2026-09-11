from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Voluntario(Base):
    """Mapeia a tabela `voluntario` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md)."""

    __tablename__ = "voluntario"

    id: Mapped[int] = mapped_column("id_voluntario", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    telefone: Mapped[str] = mapped_column(String(60))
    setor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado_civil: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(60), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(60), nullable=True)
    formacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(default=True)
