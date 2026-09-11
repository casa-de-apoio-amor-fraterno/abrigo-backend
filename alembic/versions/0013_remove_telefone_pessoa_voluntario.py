"""Remove pessoa.telefone e voluntario.telefone

Segunda etapa da normalização de telefone (ver migração 0012 e
`app/features/pessoas/pessoa.legacy.md`, seção Contatos). **Só aplicar
depois de confirmar que o ETL/backfill já copiou os dados pra
`pessoa_contato`/`voluntario_contato`** — essa migração é destrutiva
(coluna com dado real é removida), diferente do padrão aditivo do resto
do projeto. Rodar contra o dump de produção real: primeiro `alembic
upgrade` até 0012, depois `python -m app.scripts.etl_migracao ...
--confirmar` (que já popula as tabelas de contato a partir do MySQL
legado), só então seguir até esta revisão.

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-11

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("pessoa", "telefone")
    op.drop_column("voluntario", "telefone")


def downgrade() -> None:
    op.add_column("voluntario", sa.Column("telefone", sa.String(length=60), nullable=False, server_default=""))
    op.add_column("pessoa", sa.Column("telefone", sa.String(length=60), nullable=True))
