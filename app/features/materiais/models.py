from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Material(Base):
    """Mapeia a tabela `material` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `situacao` é campo de texto livre no legado (`TcxDBTextEdit`, não um
    combo com valores fixos — diferente de `estadia.situacao`) — mantido
    como `String`, não enum. Dado real observado: 'Disponível', 'Baixado',
    mas não há lista fechada de valores confirmada na UI.
    """

    __tablename__ = "material"

    id: Mapped[int] = mapped_column("id_material", primary_key=True)
    descricao: Mapped[str] = mapped_column(String(60))
    codigo_identificacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    disponivel_emprestimo: Mapped[bool] = mapped_column(default=False)
    situacao: Mapped[str] = mapped_column(String(60))
    local: Mapped[str] = mapped_column(String(20))
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool | None] = mapped_column(nullable=True, default=True)
    motivo_baixa: Mapped[str | None] = mapped_column(Text, nullable=True)
