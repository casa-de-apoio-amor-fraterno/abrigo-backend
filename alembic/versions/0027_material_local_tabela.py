"""Fecha material.local numa tabela própria (material_local)

`local` era texto livre (varchar(20)) — dado real observado tinha só 3
valores distintos: 'Casa', 'Bazar', 'Empréstimo'. Decisão do time,
2026-09-26: mesmo padrão de `Hospital` (CRUD simples id+nome), pra
permitir cadastrar novos pontos da CAAF (outra loja do bazar, etc.) sem
depender de código.

- Cria `material_local` (id, nome, ativo) e seed com os valores distintos
  já usados em `material.local`.
- Adiciona `material.id_local` (FK), backfill por nome, remove `local`.

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-26

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "material_local",
        sa.Column("id_material_local", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_material_local_nome", "material_local", ["nome"], unique=True)

    op.execute(
        sa.text(
            "INSERT INTO material_local (nome) "
            "SELECT DISTINCT local FROM material ORDER BY local"
        )
    )

    op.add_column("material", sa.Column("id_local", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE material SET id_local = material_local.id_material_local "
            "FROM material_local WHERE material.local = material_local.nome"
        )
    )
    op.alter_column("material", "id_local", nullable=False)
    op.create_foreign_key(
        "fk_material_id_local", "material", "material_local", ["id_local"], ["id_material_local"]
    )
    op.drop_column("material", "local")


def downgrade() -> None:
    op.add_column("material", sa.Column("local", sa.String(length=20), nullable=True))
    op.execute(
        sa.text(
            "UPDATE material SET local = material_local.nome "
            "FROM material_local WHERE material.id_local = material_local.id_material_local"
        )
    )
    op.alter_column("material", "local", nullable=False)
    op.drop_constraint("fk_material_id_local", "material", type_="foreignkey")
    op.drop_column("material", "id_local")
    op.drop_index("ix_material_local_nome", table_name="material_local")
    op.drop_table("material_local")
