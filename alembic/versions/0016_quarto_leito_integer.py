"""Normaliza quarto.leito pra Integer

Dado sujo (achado 2026-09-12): `leito` é `varchar` no legado, mas devia
representar a quantidade de leitos do quarto — dado real tinha valores
como `'2 leitos'`, `'00003'`, `'04'`, misturando zeros à esquerda e texto
com o número. Extrai só os dígitos de cada valor e converte pra
`Integer`. `numero` continua `varchar` (tem valor legitimamente não
numérico, ex.: `'Sala de Convivência'`), fora de escopo aqui.

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-12

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "quarto",
        "leito",
        type_=sa.Integer(),
        postgresql_using="NULLIF(regexp_replace(leito, '[^0-9]', '', 'g'), '')::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "quarto",
        "leito",
        type_=sa.String(length=60),
        postgresql_using="leito::text",
    )
