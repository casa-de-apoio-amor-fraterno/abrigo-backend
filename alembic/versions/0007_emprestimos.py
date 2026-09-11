"""Cria emprestimo e emprestimo_item

Implementa o item 6 do backlog de `docs/atividades.md` (depende de
`pessoas`, `usuarios` e `materiais`, todos já implementados). Schema
confirmado no dump de produção `sgf_abrigo` — ver
`app/features/emprestimos/emprestimo.legacy.md`.

Revision ID: 0007_emprestimos
Revises: 0006_materiais
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emprestimo",
        sa.Column("id_emprestimo", sa.Integer(), primary_key=True),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False),
        sa.Column("situacao", sa.String(length=60), nullable=False),
        sa.Column("numero_contrato", sa.String(length=60), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_emprestimo_id_pessoa", "emprestimo", ["id_pessoa"])
    op.create_index("ix_emprestimo_situacao", "emprestimo", ["situacao"])

    op.create_table(
        "emprestimo_item",
        sa.Column("id_emprestimo_item", sa.Integer(), primary_key=True),
        sa.Column(
            "id_emprestimo", sa.Integer(), sa.ForeignKey("emprestimo.id_emprestimo"), nullable=False
        ),
        sa.Column(
            "id_material", sa.Integer(), sa.ForeignKey("material.id_material"), nullable=False
        ),
        sa.Column("data_emprestimo", sa.Date(), nullable=True),
        sa.Column("data_devolucao", sa.Date(), nullable=True),
        sa.Column("situacao", sa.String(length=60), nullable=True),
        sa.Column("renovacao", sa.String(length=60), nullable=True),
    )
    op.create_index("ix_emprestimo_item_id_emprestimo", "emprestimo_item", ["id_emprestimo"])


def downgrade() -> None:
    op.drop_index("ix_emprestimo_item_id_emprestimo", "emprestimo_item")
    op.drop_table("emprestimo_item")

    op.drop_index("ix_emprestimo_situacao", "emprestimo")
    op.drop_index("ix_emprestimo_id_pessoa", "emprestimo")
    op.drop_table("emprestimo")
