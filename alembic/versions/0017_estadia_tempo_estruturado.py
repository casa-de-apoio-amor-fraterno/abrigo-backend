"""Estrutura tempo_estadia em valor + unidade

Depreciação de `estadia.tempo_estadia` (texto livre legado, usado às vezes
para observação em vez de duração — ver `estadia.legacy.md`). Cria
`tempo_estadia_valor` (inteiro) e `tempo_estadia_unidade` (dias/noites/
horas) e faz backfill a partir do texto legado só para os casos em que o
formato é reconhecível ("N dia(s)/noite(s)/hora(s)", com ou sem zero à
esquerda, número sozinho tratado como dias). O texto original é mantido
intacto na coluna antiga, sem deletar nem sobrescrever — é a fonte de
auditoria para quem não migrou (grafia irregular, texto usado como
observação, etc.).

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-12

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("estadia", sa.Column("tempo_estadia_valor", sa.Integer(), nullable=True))
    op.add_column(
        "estadia", sa.Column("tempo_estadia_unidade", sa.String(length=10), nullable=True)
    )

    # Casos "N dia(s)"/"N noite(s)"/"N hora(s)" (case-insensitive, com
    # espaços nas pontas já removidos por trim).
    op.execute(
        r"""
        UPDATE estadia
        SET tempo_estadia_valor = (regexp_match(trim(tempo_estadia), '^(\d+)\s*(dias?|noites?|horas?)$', 'i'))[1]::integer,
            tempo_estadia_unidade = CASE lower((regexp_match(trim(tempo_estadia), '^(\d+)\s*(dias?|noites?|horas?)$', 'i'))[2])
                WHEN 'dia' THEN 'dias'
                WHEN 'dias' THEN 'dias'
                WHEN 'noite' THEN 'noites'
                WHEN 'noites' THEN 'noites'
                WHEN 'hora' THEN 'horas'
                WHEN 'horas' THEN 'horas'
            END
        WHERE trim(tempo_estadia) ~* '^\d+\s*(dias?|noites?|horas?)$'
        """
    )

    # Número sozinho, sem unidade escrita (ex.: '1', '2') — decisão do time:
    # tratar como dias, unidade predominante no restante dos dados reais.
    op.execute(
        r"""
        UPDATE estadia
        SET tempo_estadia_valor = trim(tempo_estadia)::integer,
            tempo_estadia_unidade = 'dias'
        WHERE trim(tempo_estadia) ~ '^\d+$'
        """
    )


def downgrade() -> None:
    op.drop_column("estadia", "tempo_estadia_unidade")
    op.drop_column("estadia", "tempo_estadia_valor")
