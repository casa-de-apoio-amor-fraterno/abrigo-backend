from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Estado(Base):
    """Mapeia a tabela `estado` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Lista fixa das UFs brasileiras (27 registros, id = código IBGE, não
    sequencial). Sem `ativo` — não existe no dump legado.
    """

    __tablename__ = "estado"

    id: Mapped[int] = mapped_column("id_estado", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    uf: Mapped[str] = mapped_column(String(2))
