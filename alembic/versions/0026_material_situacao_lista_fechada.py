"""Fecha lista de situações de material (Baixado -> Inutilizado, + Alocado)

Situação era texto livre (ver `material.legacy.md`) com valores reais
observados: 'Disponível', 'Baixado', 'Emprestado'. Decisão do time,
2026-09-26: lista fechada (`app/features/materiais/schemas.SituacaoMaterial`)
com 'Disponível', 'Alocado', 'Emprestado', 'Inutilizado'.

- 'Baixado' -> 'Inutilizado' (renomeação, mesmo significado: item pra
  descartar, `motivo_baixa` explica o motivo).
- 'Disponível' com `local` diferente de 'Casa' (ex.: 'Bazar', outro posto
  da CAAF) -> 'Alocado': material já disponibilizado em algum lugar fora
  do Abrigo, mas ainda não emprestado a uma pessoa — estado novo, não
  existia no legado (ficava indistinguível de 'Disponível' comum).
- 'Emprestado' não muda.

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-26

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE material SET situacao = 'Inutilizado' WHERE situacao = 'Baixado'"))
    op.execute(
        sa.text(
            "UPDATE material SET situacao = 'Alocado' "
            "WHERE situacao = 'Disponível' AND local <> 'Casa'"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE material SET situacao = 'Baixado' WHERE situacao = 'Inutilizado'"))
    op.execute(sa.text("UPDATE material SET situacao = 'Disponível' WHERE situacao = 'Alocado'"))
