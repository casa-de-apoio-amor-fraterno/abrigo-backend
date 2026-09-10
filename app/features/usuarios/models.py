from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Usuario(Base):
    """Mapeia a tabela `usuario` já existente em produção (sistema legado, desde 2013).

    Não renomear/remover colunas legadas sem uma migração Alembic dedicada — o
    banco tem dados reais. `senha` é o campo legado em texto plano (ver
    `usuario.legacy.md`); `senha_hash` é a coluna nova, adicionada via
    migração aditiva, usada assim que o usuário loga pela primeira vez no
    sistema novo.
    """

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column("id_usuario", primary_key=True)
    login: Mapped[str] = mapped_column(String(50), unique=True)
    nome: Mapped[str] = mapped_column(String(150))
    perfil: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Legado — texto plano, mantido só até todo usuário logar ao menos uma vez.
    senha: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Novo — hash bcrypt, preenchido no primeiro login bem-sucedido.
    senha_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
