from sqlalchemy import ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Material(Base):
    """Mapeia a tabela `material` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `situacao` era campo de texto livre no legado (`TcxDBTextEdit`, sem
    combo de valores fixos) — decisão do time em 2026-09-26 fechou a lista
    (ver `schemas.SituacaoMaterial`): 'Disponível', 'Alocado', 'Emprestado',
    'Inutilizado' (era 'Baixado', renomeado). Mantido como `String` na
    coluna (não `Enum` do SQLAlchemy) — mesmo padrão de
    `Emprestimo.situacao`, validado só no Pydantic.

    `local` era texto livre (varchar(20)) — fechado numa tabela própria
    (`MaterialLocal`) na mesma decisão de 2026-09-26, ver
    `materiais_locais/models.py`.

    `foto`/`foto_thumb` são feature nova (sem equivalente no legado, sem
    dado real pra migrar) — mesmo padrão de `Pessoa.foto` (BLOB no próprio
    Postgres, opcional), mas com upload de arquivo do PC em vez de captura
    por webcam, e com uma miniatura gerada no servidor (`foto_thumb`, via
    Pillow) pra não trafegar a imagem inteira na listagem.
    """

    __tablename__ = "material"

    id: Mapped[int] = mapped_column("id_material", primary_key=True)
    descricao: Mapped[str] = mapped_column(String(60))
    numero_patrimonio: Mapped[str | None] = mapped_column(String(60), nullable=True)
    disponivel_emprestimo: Mapped[bool] = mapped_column(default=False)
    situacao: Mapped[str] = mapped_column(String(60))
    id_local: Mapped[int] = mapped_column(ForeignKey("material_local.id_material_local"))
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool | None] = mapped_column(nullable=True, default=True)
    motivo_baixa: Mapped[str | None] = mapped_column(Text, nullable=True)
    foto: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    foto_thumb: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    foto_content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    @property
    def tem_foto(self) -> bool:
        return self.foto is not None
