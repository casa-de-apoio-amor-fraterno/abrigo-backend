"""Adiciona usuario.senha_hash (migração aditiva, não mexe em usuario.senha)

O sistema legado guarda a senha em texto plano na coluna `usuario.senha`
(ver app/features/usuarios/usuario.legacy.md). Esta migração só adiciona a
coluna nova, nullable — a coluna antiga continua existindo e sendo usada
como fallback até cada usuário logar ao menos uma vez no sistema novo (ver
app/features/auth/service.py).

Revision ID: 0002_add_usuario_senha_hash
Revises: 0001_baseline
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_add_usuario_senha_hash"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("senha_hash", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("usuario", "senha_hash")
