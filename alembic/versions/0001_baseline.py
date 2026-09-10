"""Baseline — marca o schema já existente em produção (banco em uso desde 2013)

Esta migração não cria nem altera nenhuma tabela. Ela só existe para que o
Alembic tenha um ponto de partida (`alembic stamp 0001_baseline`) sobre o
banco de produção, que já tem as tabelas do sistema legado (Delphi/Argos).

Toda migração futura deve ser ADITIVA sobre esse schema (ALTER TABLE ADD
COLUMN, novas tabelas) — nunca DROP/CREATE de tabelas que já têm dados reais,
a não ser que o dado tenha sido migrado para o lugar novo antes.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
