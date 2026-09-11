"""Cria pessoa_contato e voluntario_contato

Normaliza telefone numa tabela própria (2026-09-11) — `pessoa.telefone` e
`voluntario.telefone` legados eram `varchar(60)` texto livre sem nenhuma
estrutura (um único `TcxDBTextEdit` no Delphi, sem máscara), e o dado real
de produção mistura múltiplos números, nome de quem atende e observações
no mesmo campo. Ver `app/features/pessoas/pessoa.legacy.md` (seção
Contatos) e `app/scripts/etl/transformacoes.parse_contatos` (heurística de
separação usada no ETL).

Migração aditiva — as colunas `telefone` antigas só são removidas na
migração seguinte (0013), depois de confirmado que os dados foram
copiados pra cá.

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-11

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pessoa_contato",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("numero", sa.String(length=60), nullable=False),
        sa.Column("nome_contato", sa.String(length=60), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "voluntario_contato",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "id_voluntario", sa.Integer(), sa.ForeignKey("voluntario.id_voluntario"), nullable=False
        ),
        sa.Column("numero", sa.String(length=60), nullable=False),
        sa.Column("nome_contato", sa.String(length=60), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("voluntario_contato")
    op.drop_table("pessoa_contato")
