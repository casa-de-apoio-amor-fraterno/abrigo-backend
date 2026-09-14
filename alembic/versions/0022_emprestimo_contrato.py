"""Cria emprestimo_contrato

Termo de responsabilidade assinado pela pessoa que toma o(s) material(is)
emprestado(s) — feature nova, sem equivalente no legado (que só guardava
`emprestimo.numero_contrato` como texto livre; o termo em si, se existia,
era feito em papel fora do sistema). Um empréstimo tem no máximo um
contrato (`id_emprestimo` único) — decisão do usuário: assina uma vez, na
criação; renovação/alteração de item não gera novo termo. `pdf` guarda o
documento já assinado, congelado no momento da assinatura (editar o
empréstimo depois não deve alterar o que já foi assinado). Ver
`app/features/emprestimos/models.py` (`EmprestimoContrato`).

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-14

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emprestimo_contrato",
        sa.Column("id_emprestimo_contrato", sa.Integer(), primary_key=True),
        sa.Column(
            "id_emprestimo",
            sa.Integer(),
            sa.ForeignKey("emprestimo.id_emprestimo"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False
        ),
        sa.Column("assinatura", sa.LargeBinary(), nullable=False),
        sa.Column("pdf", sa.LargeBinary(), nullable=False),
        sa.Column("data_assinatura", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("emprestimo_contrato")
