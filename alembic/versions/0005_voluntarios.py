"""Cria voluntario

Implementa o item 4 do backlog de `docs/atividades.md` (CRUD simples, sem
dependências, 40 registros). Schema confirmado no dump de produção
`sgf_abrigo` — ver `app/features/voluntarios/voluntario.legacy.md`.

Revision ID: 0005_voluntarios
Revises: 0004_estadias
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "voluntario",
        sa.Column("id_voluntario", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("telefone", sa.String(length=60), nullable=False),
        sa.Column("setor", sa.String(length=60), nullable=True),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("estado_civil", sa.String(length=60), nullable=True),
        sa.Column("cpf", sa.String(length=60), nullable=True),
        sa.Column("endereco", sa.String(length=60), nullable=True),
        sa.Column("formacao", sa.String(length=60), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_voluntario_nome", "voluntario", ["nome"])
    op.create_index("ix_voluntario_cpf", "voluntario", ["cpf"])


def downgrade() -> None:
    op.drop_index("ix_voluntario_cpf", "voluntario")
    op.drop_index("ix_voluntario_nome", "voluntario")
    op.drop_table("voluntario")
