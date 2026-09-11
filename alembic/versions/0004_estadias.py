"""Cria estadia e estadia_acompanhante

Implementa o item 3 do backlog de `docs/atividades.md` — feature central do
abrigo (~4.434 registros). Schema confirmado no dump de produção
`sgf_abrigo` — ver `app/features/estadias/estadia.legacy.md`, que também
documenta a resolução do achado 3 (tipo_pessoa × estadia_acompanhante: são
conceitos diferentes, mantidos os dois) e do achado 1 (acompanhamento não
vira tabela própria — dados reconciliados na ETL).

Revision ID: 0004_estadias
Revises: 0003_quartos
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "estadia",
        sa.Column("id_estadia", sa.Integer(), primary_key=True),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("id_quarto", sa.Integer(), sa.ForeignKey("quarto.id_quarto"), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("usuario.id_usuario"), nullable=False),
        sa.Column("data_entrada", sa.DateTime(), nullable=False),
        sa.Column("data_saida", sa.DateTime(), nullable=True),
        sa.Column("tempo_estadia", sa.String(length=60), nullable=True),
        sa.Column("tipo_pessoa", sa.String(length=20), nullable=False, server_default="Paciente"),
        sa.Column("situacao", sa.String(length=30), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=True, server_default=sa.true()),
    )
    op.create_index("ix_estadia_id_pessoa", "estadia", ["id_pessoa"])
    op.create_index("ix_estadia_situacao", "estadia", ["situacao"])

    op.create_table(
        "estadia_acompanhante",
        sa.Column("id_estadia_acompanhante", sa.Integer(), primary_key=True),
        sa.Column(
            "id_estadia", sa.Integer(), sa.ForeignKey("estadia.id_estadia"), nullable=False
        ),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("data_entrada", sa.DateTime(), nullable=False),
        sa.Column("data_saida", sa.DateTime(), nullable=True),
        sa.Column("grau_parentesco", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_estadia_acompanhante_id_estadia", "estadia_acompanhante", ["id_estadia"]
    )


def downgrade() -> None:
    op.drop_index("ix_estadia_acompanhante_id_estadia", "estadia_acompanhante")
    op.drop_table("estadia_acompanhante")

    op.drop_index("ix_estadia_situacao", "estadia")
    op.drop_index("ix_estadia_id_pessoa", "estadia")
    op.drop_table("estadia")
