"""Cria emprestimo_historico

Espelha `Scripts/Atualização Setembro 2026/Criar tabela
emprestimo_historico.sql` do legado (2026-09-09) — trilha de auditoria de
alterações do empréstimo (observação, itens), ainda não presente no dump
de produção usado na migração inicial (`sgf_abrigo`). Ver
`app/features/emprestimos/models.py` (`EmprestimoHistorico`).

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-11

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emprestimo_historico",
        sa.Column("id_emprestimo_historico", sa.Integer(), primary_key=True),
        sa.Column(
            "id_emprestimo",
            sa.Integer(),
            sa.ForeignKey("emprestimo.id_emprestimo"),
            nullable=False,
        ),
        sa.Column(
            "id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False
        ),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=False),
        sa.Column("data_cadastro", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_emprestimo_historico_id_emprestimo", "emprestimo_historico", ["id_emprestimo"]
    )


def downgrade() -> None:
    op.drop_index("ix_emprestimo_historico_id_emprestimo", "emprestimo_historico")
    op.drop_table("emprestimo_historico")
