"""Torna pessoa.data_cadastro opcional

Achado ao testar o ETL contra o dump real de produção (2026-09-10): 444 de
5.326 pessoas (~8,3%) têm `data_cadastro = '0000-00-00'` no MySQL legado —
o ETL mapeia isso pra `NULL` (ver
`app/scripts/etl/transformacoes.data_zerada_para_none`), mas o model
`Pessoa.data_cadastro` era `NOT NULL`, o que rejeitava essas linhas. Ver
`app/features/pessoas/pessoa.legacy.md`.

Revision ID: 0009_pessoa_data_cadastro_nullable
Revises: 0008_avaliacao_social_composicao_familiar
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0009_pessoa_data_cadastro_nullable"
down_revision = "0008_avaliacao_social_composicao_familiar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("pessoa", "data_cadastro", existing_type=sa.Date(), nullable=True)


def downgrade() -> None:
    op.alter_column("pessoa", "data_cadastro", existing_type=sa.Date(), nullable=False)
