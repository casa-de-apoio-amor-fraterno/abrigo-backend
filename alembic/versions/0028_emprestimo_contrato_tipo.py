"""Permite múltiplos contratos por empréstimo (tipo Comodato/Renovação)

Decisão do time, 2026-09-26: além do termo de comodato original, agora dá
pra assinar um termo aditivo de renovação de prazo a cada vez que o
empréstimo é prorrogado — sem limite de quantos. Reverte a regra anterior
de "no máximo um contrato por empréstimo" (migração 0022).

Registros já existentes são todos do tipo original — `tipo` recebe
'Comodato' por padrão.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-26

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emprestimo_contrato",
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="Comodato"),
    )
    op.alter_column("emprestimo_contrato", "tipo", server_default=None)
    op.drop_constraint(
        "emprestimo_contrato_id_emprestimo_key", "emprestimo_contrato", type_="unique"
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "emprestimo_contrato_id_emprestimo_key", "emprestimo_contrato", ["id_emprestimo"]
    )
    op.drop_column("emprestimo_contrato", "tipo")
