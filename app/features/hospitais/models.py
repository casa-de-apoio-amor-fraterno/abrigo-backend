from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Hospital(Base):
    """Mapeia a tabela `hospital` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Apesar do nome, também é usado como categoria genérica de
    origem/encaminhamento da pessoa (ex.: "Empréstimo Solidário", "Doação de
    fralda" aparecem como registros reais) — mantido fiel ao dado legado.
    """

    __tablename__ = "hospital"

    id: Mapped[int] = mapped_column("id_hospital", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(default=True)
