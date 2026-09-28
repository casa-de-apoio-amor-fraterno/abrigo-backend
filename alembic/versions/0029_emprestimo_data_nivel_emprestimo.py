"""Move data_emprestimo/data_devolucao/data_devolucao_efetiva de emprestimo_item pra emprestimo

Decisão do time (2026-09-28): as datas do aluguel viviam em
`emprestimo_item` (uma por item), sem equivalente no legado. Isso quebrava
o cálculo do prazo de vigência do contrato de renovação
(`service._prazo_vigencia_contrato`) quando um empréstimo tinha vários
itens com prazos distintos (ex.: um item de 20 dias e outro de 40 dias no
mesmo empréstimo) — o min/max entre itens não representava um prazo único
e coerente pro contrato. Solução: um único prazo por empréstimo.

Backfill (caso 1:N emprestimo x itens já migrado): pra cada empréstimo,
usa as datas do item de **maior peso** — o item cujo intervalo
`data_devolucao - data_emprestimo` é o maior entre os itens daquele
empréstimo (ex.: item de 40 dias vence sobre o de 20). Itens sem as duas
datas ficam por último (`NULLS LAST`); em empate, o item mais recente
(maior id) desempata.

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-28

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emprestimo", sa.Column("data_emprestimo", sa.Date(), nullable=True))
    op.add_column("emprestimo", sa.Column("data_devolucao", sa.Date(), nullable=True))
    op.add_column("emprestimo", sa.Column("data_devolucao_efetiva", sa.Date(), nullable=True))

    op.execute(
        """
        UPDATE emprestimo e
        SET data_emprestimo = escolhido.data_emprestimo,
            data_devolucao = escolhido.data_devolucao,
            data_devolucao_efetiva = escolhido.data_devolucao_efetiva
        FROM (
            SELECT DISTINCT ON (id_emprestimo)
                id_emprestimo, data_emprestimo, data_devolucao, data_devolucao_efetiva
            FROM emprestimo_item
            ORDER BY id_emprestimo,
                (data_devolucao - data_emprestimo) DESC NULLS LAST,
                id_emprestimo_item DESC
        ) escolhido
        WHERE e.id_emprestimo = escolhido.id_emprestimo
        """
    )

    op.drop_column("emprestimo_item", "data_emprestimo")
    op.drop_column("emprestimo_item", "data_devolucao")
    op.drop_column("emprestimo_item", "data_devolucao_efetiva")


def downgrade() -> None:
    op.add_column("emprestimo_item", sa.Column("data_emprestimo", sa.Date(), nullable=True))
    op.add_column("emprestimo_item", sa.Column("data_devolucao", sa.Date(), nullable=True))
    op.add_column("emprestimo_item", sa.Column("data_devolucao_efetiva", sa.Date(), nullable=True))

    # Aproximação: todos os itens do empréstimo voltam a apontar pra mesma
    # data única do cabeçalho — não há como recuperar os prazos individuais
    # por item depois do backfill/drop acima.
    op.execute(
        """
        UPDATE emprestimo_item ei
        SET data_emprestimo = e.data_emprestimo,
            data_devolucao = e.data_devolucao,
            data_devolucao_efetiva = e.data_devolucao_efetiva
        FROM emprestimo e
        WHERE ei.id_emprestimo = e.id_emprestimo
        """
    )

    op.drop_column("emprestimo", "data_devolucao_efetiva")
    op.drop_column("emprestimo", "data_devolucao")
    op.drop_column("emprestimo", "data_emprestimo")
