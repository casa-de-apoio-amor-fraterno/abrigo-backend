"""Adiciona ocupa_leito em estadia_acompanhante

Um acompanhante pode, opcionalmente, também ocupar um dos leitos do
quarto do paciente (diferente de `Estadia.tipo_pessoa == ACOMPANHANTE`,
que é uma `Estadia` própria com leito próprio — aqui é o mesmo registro
da lista de acompanhantes). Usado pra colorir esse leito diferente no
painel de ocupação (tela Início). Decisão do time, 2026-09-25.

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-25

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "estadia_acompanhante",
        sa.Column("ocupa_leito", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # server_default só existe pra popular as linhas já existentes sem
    # exigir um valor na hora do ALTER — daqui pra frente o valor vem
    # sempre explícito da aplicação (mesmo padrão de `ativo` em outras
    # tabelas), então removemos o default do lado do banco.
    op.alter_column("estadia_acompanhante", "ocupa_leito", server_default=None)


def downgrade() -> None:
    op.drop_column("estadia_acompanhante", "ocupa_leito")
