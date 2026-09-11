"""Cria estado, hospital, municipio + FKs reais em pessoa

Implementa o item 1 do backlog de `docs/atividades.md` (tabelas de apoio,
pré-requisito pra exibir nome do estado/município/hospital na tela de
pessoa em vez do ID cru). Schema confirmado no dump de produção
`sgf_abrigo` — ver `app/features/estados/estado.legacy.md`,
`app/features/hospitais/hospital.legacy.md` e
`app/features/municipios/municipio.legacy.md`.

Como no Postgres novo (`0001_estrutura_inicial`), essas tabelas nascem
vazias — os dados reais entram depois via ETL, não por esta migração.

`pessoa.id_hospital`/`id_municipio`/`id_estado` já existiam como inteiros
soltos (criados em 0001); esta migração adiciona as foreign keys de verdade
agora que as tabelas referenciadas existem.

Revision ID: 0002_estados_municipios_hospitais
Revises: 0001_estrutura_inicial
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_estados_municipios_hospitais"
down_revision = "0001_estrutura_inicial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estado",
        sa.Column("id_estado", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
    )

    op.create_table(
        "hospital",
        sa.Column("id_hospital", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "municipio",
        sa.Column("id_municipio", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("nome", sa.String(length=61), nullable=False),
        sa.Column(
            "id_estado",
            sa.Integer(),
            sa.ForeignKey("estado.id_estado"),
            nullable=False,
        ),
    )
    op.create_index("ix_municipio_id_estado", "municipio", ["id_estado"])
    op.create_index("ix_municipio_nome", "municipio", ["nome"])

    op.create_foreign_key(
        "fk_pessoa_hospital", "pessoa", "hospital", ["id_hospital"], ["id_hospital"]
    )
    op.create_foreign_key(
        "fk_pessoa_municipio", "pessoa", "municipio", ["id_municipio"], ["id_municipio"]
    )
    op.create_foreign_key(
        "fk_pessoa_estado", "pessoa", "estado", ["id_estado"], ["id_estado"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_pessoa_estado", "pessoa", type_="foreignkey")
    op.drop_constraint("fk_pessoa_municipio", "pessoa", type_="foreignkey")
    op.drop_constraint("fk_pessoa_hospital", "pessoa", type_="foreignkey")

    op.drop_index("ix_municipio_nome", "municipio")
    op.drop_index("ix_municipio_id_estado", "municipio")
    op.drop_table("municipio")
    op.drop_table("hospital")
    op.drop_table("estado")
