"""Adiciona foto/thumb em material

Feature nova (sem equivalente no legado, sem dado real pra migrar — ver
`material.legacy.md`), mesmo padrão de `Pessoa.foto` (BLOB no próprio
Postgres, opcional), mas com upload de arquivo do PC (não captura por
webcam) e uma miniatura gerada no servidor (`foto_thumb`) pra listagem.

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-12

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("material", sa.Column("foto", sa.LargeBinary(), nullable=True))
    op.add_column("material", sa.Column("foto_thumb", sa.LargeBinary(), nullable=True))
    op.add_column("material", sa.Column("foto_content_type", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("material", "foto_content_type")
    op.drop_column("material", "foto_thumb")
    op.drop_column("material", "foto")
