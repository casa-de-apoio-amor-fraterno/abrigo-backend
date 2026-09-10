"""Estrutura inicial no PostgreSQL (usuario, pessoa) + extensão pgvector

Decisão (2026-09-10): migrar de MySQL 5.5 (legado, desde 2013) para
PostgreSQL + pgvector, em vez de seguir com MySQL 8/9 ou um banco vetorial
separado. Ver docs/migracao-postgres.md para a análise completa.

Diferente das migrações que faríamos num upgrade in-place do MySQL (que
precisariam ser só ADD COLUMN sobre tabelas já existentes com dado real),
aqui o banco Postgres começa vazio — então esta migração CRIA as tabelas.
Os dados de produção são carregados depois, via ETL (pgloader) a partir do
dump do MySQL legado, não por esta migração.

Revision ID: 0001_estrutura_inicial
Revises:
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_estrutura_inicial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "usuario",
        sa.Column("id_usuario", sa.Integer(), primary_key=True),
        sa.Column("login", sa.String(length=60), nullable=False, unique=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("perfil", sa.String(length=20), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("senha", sa.String(length=60), nullable=True),
        sa.Column("senha_hash", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "pessoa",
        sa.Column("id_pessoa", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=False),
        sa.Column("rg", sa.String(length=15), nullable=True),
        sa.Column("cpf", sa.String(length=11), nullable=True),
        sa.Column("profissao", sa.String(length=60), nullable=True),
        sa.Column("cartao_sus", sa.String(length=60), nullable=True),
        sa.Column("endereco", sa.String(length=60), nullable=True),
        sa.Column("ponto_referencia", sa.String(length=60), nullable=True),
        sa.Column("telefone", sa.String(length=60), nullable=True),
        sa.Column("id_hospital", sa.Integer(), nullable=True),
        sa.Column("id_municipio", sa.Integer(), nullable=True),
        sa.Column("id_estado", sa.Integer(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("acompanhamento_social", sa.Text(), nullable=True),
        sa.Column("data_cadastro", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_pessoa_nome", "pessoa", ["nome"])
    op.create_index("ix_pessoa_cpf", "pessoa", ["cpf"])


def downgrade() -> None:
    op.drop_table("pessoa")
    op.drop_table("usuario")
    op.execute("DROP EXTENSION IF EXISTS vector")
