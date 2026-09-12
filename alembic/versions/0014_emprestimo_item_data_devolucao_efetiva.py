"""Adiciona emprestimo_item.data_devolucao_efetiva

`data_devolucao` sempre foi **prevista**, não a data real da devolução — no
legado (`untFrmManutencaoEmprestimo`) ela é digitada manualmente no mesmo
formulário e momento que `data_emprestimo`, sem nenhum fluxo que a atualize
quando o item é devolvido de fato. Confirmado com dado real (`abrigo_teste`):
itens com `situacao='Pendente'` (ainda emprestados) já tinham
`data_devolucao` no passado. Esta coluna, nova (sem equivalente no legado),
é gravada automaticamente pelo backend quando `situacao` passa a
"Devolvido" — ver `app/features/emprestimos/service.py`
(`_aplicar_devolucao_efetiva`).

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-11

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emprestimo_item", sa.Column("data_devolucao_efetiva", sa.Date(), nullable=True)
    )
    # Backfill: para itens já "Devolvido" antes desta migração, não há como
    # saber a data real — aproxima usando a data prevista (mesma lógica de
    # aproximação documentada já usada em `EstadiaAcompanhante.data_entrada`,
    # ver `project-abrigo-migration`), deixando claro no comentário da
    # coluna que é só uma estimativa retroativa.
    op.execute(
        "UPDATE emprestimo_item SET data_devolucao_efetiva = data_devolucao "
        "WHERE situacao = 'Devolvido' AND data_devolucao IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("emprestimo_item", "data_devolucao_efetiva")
