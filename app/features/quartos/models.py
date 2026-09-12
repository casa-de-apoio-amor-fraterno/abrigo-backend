from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Quarto(Base):
    """Mapeia a tabela `quarto` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `numero` é `varchar`, não numérico, apesar do nome — o dado real tem
    valores como "Sala de Convivência" (ver `quarto.legacy.md`). Mantido
    como string, fiel ao dado legado.

    `leito` (quantidade de leitos do quarto) era `varchar` no legado, com
    dado sujo (`"2 leitos"`, `"00003"`, `"04"`) — normalizado pra
    `Integer` na migração `0016`, extraindo só os dígitos de cada valor
    (ver `quarto.legacy.md`).
    """

    __tablename__ = "quarto"

    id: Mapped[int] = mapped_column("id_quarto", primary_key=True)
    descricao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    numero: Mapped[str] = mapped_column(String(60))
    leito: Mapped[int] = mapped_column(Integer)
    ativo: Mapped[bool] = mapped_column(default=True)
