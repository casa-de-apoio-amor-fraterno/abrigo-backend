"""Link de assinatura remota do contrato de comodato

Pedido do time (2026-10-01): gerar um link pra a pessoa assinar o contrato
pendente pelo próprio celular, informando o CPF, sem login. Guarda só o
hash do token (ver `EmprestimoLinkAssinatura`).

Revision ID: 0031
Revises: 0030
Create Date: 2026-10-01

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emprestimo_link_assinatura",
        sa.Column("id_emprestimo_link_assinatura", sa.Integer(), primary_key=True),
        sa.Column("id_emprestimo", sa.Integer(), sa.ForeignKey("emprestimo.id_emprestimo"), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("tentativas_cpf", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usado_em", sa.DateTime(), nullable=True),
        sa.Column("revogado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_emprestimo_link_assinatura_token_hash", "emprestimo_link_assinatura", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_emprestimo_link_assinatura_id_emprestimo", "emprestimo_link_assinatura", ["id_emprestimo"]
    )


def downgrade() -> None:
    op.drop_index("ix_emprestimo_link_assinatura_id_emprestimo", table_name="emprestimo_link_assinatura")
    op.drop_index("ix_emprestimo_link_assinatura_token_hash", table_name="emprestimo_link_assinatura")
    op.drop_table("emprestimo_link_assinatura")
