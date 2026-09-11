"""Cria avaliacao_social e composicao_familiar

Implementa o item 7 do backlog de `docs/atividades.md` — sub-rotinas de
`pessoa` com controle de acesso restrito à assistente social (regra nova,
o legado não implementava isso). Ver
`app/features/avaliacao_social/avaliacao_social.legacy.md` e
`app/features/composicao_familiar/composicao_familiar.legacy.md`.

Revision ID: 0008_avaliacao_social_composicao_familiar
Revises: 0007_emprestimos
Create Date: 2026-09-10

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_avaliacao_social_composicao_familiar"
down_revision = "0007_emprestimos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "avaliacao_social",
        sa.Column("id_avaliacao_social", sa.Integer(), primary_key=True),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("fumante", sa.Boolean(), nullable=True),
        sa.Column("residencia", sa.String(length=10), nullable=True),
        sa.Column("energia_eletrica", sa.Boolean(), nullable=True),
        sa.Column("agua_encanada", sa.Boolean(), nullable=True),
        sa.Column("tipo_construcao", sa.String(length=10), nullable=True),
        sa.Column("renda_mensal_familiar", sa.String(length=60), nullable=True),
        sa.Column("quantas_pessoas_contribuem_formacao_renda", sa.String(length=60), nullable=True),
        sa.Column(
            "alguem_recebe_beneficio_previdenciario_governo", sa.String(length=60), nullable=True
        ),
        sa.Column("diagnostico", sa.Text(), nullable=True),
        sa.Column("tratamento_realizado", sa.Text(), nullable=True),
        sa.Column("casos_cancer_familia", sa.Text(), nullable=True),
        sa.Column("necessita_medicamento_uso_continuo", sa.Boolean(), nullable=True),
        sa.Column("medicamento_disponibilizado_sus", sa.Boolean(), nullable=True),
        sa.Column("custo_mensal_medicamento", sa.String(length=60), nullable=True),
        sa.Column("alimentacao_especifica", sa.Text(), nullable=True),
        sa.Column("equipamento_para_locomocao", sa.Text(), nullable=True),
        sa.Column("data_movimento", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_avaliacao_social_id_pessoa", "avaliacao_social", ["id_pessoa"])

    op.create_table(
        "composicao_familiar",
        sa.Column("id_composicao_familiar", sa.Integer(), primary_key=True),
        sa.Column("id_pessoa", sa.Integer(), sa.ForeignKey("pessoa.id_pessoa"), nullable=False),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("idade", sa.String(length=60), nullable=True),
        sa.Column("grau_parentesco", sa.String(length=60), nullable=False),
        sa.Column("estado_civil", sa.String(length=60), nullable=True),
        sa.Column("renda", sa.String(length=60), nullable=True),
        sa.Column("ocupacao", sa.String(length=60), nullable=True),
    )
    op.create_index("ix_composicao_familiar_id_pessoa", "composicao_familiar", ["id_pessoa"])


def downgrade() -> None:
    op.drop_index("ix_composicao_familiar_id_pessoa", "composicao_familiar")
    op.drop_table("composicao_familiar")

    op.drop_index("ix_avaliacao_social_id_pessoa", "avaliacao_social")
    op.drop_table("avaliacao_social")
