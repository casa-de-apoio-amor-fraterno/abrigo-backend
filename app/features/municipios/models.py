from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Municipio(Base):
    """Mapeia a tabela `municipio` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    ~5.570 registros fixos (tabela IBGE completa), id = código IBGE de 7
    dígitos. Sem `ativo` — não existe no dump legado. Nomes mantidos fiéis
    ao dado de origem, mesmo com grafia irregular (ex.: "Alta Floresta
    DOeste").
    """

    __tablename__ = "municipio"

    id: Mapped[int] = mapped_column("id_municipio", primary_key=True)
    nome: Mapped[str] = mapped_column(String(61))
    id_estado: Mapped[int] = mapped_column(ForeignKey("estado.id_estado"))
