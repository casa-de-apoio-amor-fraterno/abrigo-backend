"""Índices pra acelerar /api/emprestimos/alertas-vencimento e listar()

Reportado como lento em produção (Render, 2026-09-28, ~7.35s). Contra o
dado real local (`abrigo_teste`, ~2.5k empréstimos/~3.5k itens) o
`EXPLAIN ANALYZE` da mesma consulta já roda em poucos milissegundos com
`seq scan` (tabela pequena demais pro planner preferir índice) — o tempo
alto reportado é mais provável de ser cold start do Render free tier (o
serviço "dorme" sem tráfego) do que falta de índice. Ainda assim, os
índices abaixo são baratos e corretos pro padrão de acesso real da
consulta (`service.listar_alertas_vencimento`/`service.listar`):
`WHERE emprestimo.ativo AND emprestimo.data_devolucao <= :limite ORDER BY
emprestimo.data_devolucao` e `WHERE emprestimo_item.situacao !=
'Devolvido'`.

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-28

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composto (não dois índices separados): a consulta sempre filtra os
    # dois juntos (`ativo AND data_devolucao <= :limite`) e já ordena por
    # `data_devolucao` — um índice composto cobre filtro e ordenação numa
    # única leitura, o que dois índices simples não fariam sem um "bitmap
    # and" adicional.
    op.create_index("ix_emprestimo_ativo_data_devolucao", "emprestimo", ["ativo", "data_devolucao"])
    op.create_index("ix_emprestimo_item_situacao", "emprestimo_item", ["situacao"])


def downgrade() -> None:
    op.drop_index("ix_emprestimo_item_situacao", "emprestimo_item")
    op.drop_index("ix_emprestimo_ativo_data_devolucao", "emprestimo")
