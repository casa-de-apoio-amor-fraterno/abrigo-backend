"""Cria material

Implementa o item 5 do backlog de `docs/atividades.md` (CRUD simples,
~1.710 registros, pré-requisito de `emprestimos`). Schema confirmado no
dump de produção `sgf_abrigo` — ver
`app/features/materiais/material.legacy.md`.

Revision ID: 0006_materiais
Revises: 0005_voluntarios
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_materiais"
down_revision = "0005_voluntarios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "material",
        sa.Column("id_material", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=60), nullable=False),
        sa.Column("codigo_identificacao", sa.String(length=60), nullable=True),
        sa.Column("disponivel_emprestimo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("situacao", sa.String(length=60), nullable=False),
        sa.Column("local", sa.String(length=20), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column("motivo_baixa", sa.Text(), nullable=True),
    )
    op.create_index("ix_material_descricao", "material", ["descricao"])
    op.create_index("ix_material_codigo_identificacao", "material", ["codigo_identificacao"])


def downgrade() -> None:
    op.drop_index("ix_material_codigo_identificacao", "material")
    op.drop_index("ix_material_descricao", "material")
    op.drop_table("material")
