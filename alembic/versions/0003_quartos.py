"""Cria quarto

Implementa o item 2 do backlog de `docs/atividades.md` (pré-requisito de
`estadia`, que referencia `quarto.id_quarto`). Schema confirmado no dump de
produção `sgf_abrigo` — ver `app/features/quartos/quarto.legacy.md`.

`numero` e `leito` ficam como `String`, não `Integer`, apesar dos nomes —
o dado real de produção tem valores não numéricos (ex.: "2 leitos",
"Sala de Convivência").

Revision ID: 0003_quartos
Revises: 0002_estados_municipios_hospitais
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quarto",
        sa.Column("id_quarto", sa.Integer(), primary_key=True),
        sa.Column("descricao", sa.String(length=60), nullable=True),
        sa.Column("numero", sa.String(length=60), nullable=False),
        sa.Column("leito", sa.String(length=60), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("quarto")
