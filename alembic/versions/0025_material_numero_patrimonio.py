"""Renomeia codigo_identificacao para numero_patrimonio em material

O campo é o número do patrimônio do item (ver
`app/features/materiais/material.legacy.md`) — nome antigo
(`codigo_identificacao`) causava confusão com o cadastro de empréstimos,
onde esse número é essencial pra identificar o item no contrato. Decisão
do time, 2026-09-25.

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-25

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("material", "codigo_identificacao", new_column_name="numero_patrimonio")
    op.drop_index("ix_material_codigo_identificacao", table_name="material")
    op.create_index("ix_material_numero_patrimonio", "material", ["numero_patrimonio"])


def downgrade() -> None:
    op.drop_index("ix_material_numero_patrimonio", table_name="material")
    op.create_index("ix_material_codigo_identificacao", "material", ["codigo_identificacao"])
    op.alter_column("material", "numero_patrimonio", new_column_name="codigo_identificacao")
