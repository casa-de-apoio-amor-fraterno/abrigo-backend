from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Usuario(Base):
    """Mapeia a tabela `usuario` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `senha` é o campo legado em texto plano (ver `usuario.legacy.md`);
    `senha_hash` é a coluna nova, usada assim que o usuário loga pela
    primeira vez no sistema novo.
    """

    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column("id_usuario", primary_key=True)
    login: Mapped[str] = mapped_column(String(60), unique=True)
    nome: Mapped[str] = mapped_column(String(60))
    perfil: Mapped[str] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(default=True)

    # Legado — texto plano, mantido só até todo usuário logar ao menos uma vez.
    senha: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Novo — hash bcrypt, preenchido no primeiro login bem-sucedido.
    senha_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
