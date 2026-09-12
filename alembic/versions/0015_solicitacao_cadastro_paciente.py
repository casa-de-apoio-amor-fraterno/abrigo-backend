"""Adiciona solicitacao_cadastro_paciente

Feature nova (2026-09-12), sem equivalente no legado — auto-cadastro
público de paciente pelo próprio celular (tela de login, opção "Sou
paciente"). Fica pendente de aprovação de um usuário do sistema antes de
virar `Pessoa` de verdade — ver `app/features/solicitacoes_cadastro/`.

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-12

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "solicitacao_cadastro_paciente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=True),
        sa.Column("telefone", sa.String(length=60), nullable=True),
        sa.Column("foto", sa.LargeBinary(), nullable=True),
        sa.Column("foto_content_type", sa.String(length=50), nullable=True),
        sa.Column("situacao", sa.String(length=20), nullable=False),
        sa.Column("data_solicitacao", sa.DateTime(), nullable=False),
        sa.Column(
            "id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=True
        ),
        sa.Column(
            "id_usuario_analise",
            sa.Integer(),
            sa.ForeignKey("usuario.id_usuario"),
            nullable=True,
        ),
        sa.Column("data_analise", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("solicitacao_cadastro_paciente")
