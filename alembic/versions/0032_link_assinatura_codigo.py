"""Código curto no link de assinatura remota

Pedido do time (2026-10-01): botão "Assinar contrato" na tela de login, onde
a pessoa digita um código curto (em vez de abrir o link) e confirma o CPF.
Guardado só como hash, igual ao token.

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-01

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emprestimo_link_assinatura", sa.Column("codigo_hash", sa.String(length=64), nullable=True))
    op.create_index(
        "ix_emprestimo_link_assinatura_codigo_hash", "emprestimo_link_assinatura", ["codigo_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_emprestimo_link_assinatura_codigo_hash", table_name="emprestimo_link_assinatura")
    op.drop_column("emprestimo_link_assinatura", "codigo_hash")
