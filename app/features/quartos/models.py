from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Quarto(Base):
    """Mapeia a tabela `quarto` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `numero` e `leito` são `varchar`, não numéricos, apesar dos nomes — o
    dado real tem valores como "2 leitos", "Sala de Convivência", "00003"
    (ver `quarto.legacy.md`). Mantidos como string, fiéis ao dado legado.
    """

    __tablename__ = "quarto"

    id: Mapped[int] = mapped_column("id_quarto", primary_key=True)
    descricao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    numero: Mapped[str] = mapped_column(String(60))
    leito: Mapped[str] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(default=True)
