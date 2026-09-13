"""Cria estadia_historico

Roadmap de tudo que ocorreu durante a estadia — mesmo padrão de
`emprestimo_historico` (0010), sem equivalente no legado. Motivador: hoje a
única trilha de eventos de uma estadia é o campo `observacao` livre, que
qualquer edição sobrescreve sem deixar rastro do valor anterior. Registrada
automaticamente em `service.py` (`_registrar_historico`) na criação,
alteração de campos e encerramento da estadia. Ver
`app/features/estadias/models.py` (`EstadiaHistorico`).

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-13

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estadia_historico",
        sa.Column("id_estadia_historico", sa.Integer(), primary_key=True),
        sa.Column(
            "id_estadia", sa.Integer(), sa.ForeignKey("estadia.id_estadia"), nullable=False
        ),
        sa.Column(
            "id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False
        ),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=False),
        sa.Column("data_cadastro", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_estadia_historico_id_estadia", "estadia_historico", ["id_estadia"])


def downgrade() -> None:
    op.drop_index("ix_estadia_historico_id_estadia", "estadia_historico")
    op.drop_table("estadia_historico")
