"""Move hospital de Pessoa pra Estadia + concatena observação

Achado do time (2026-09-13): `pessoa.id_hospital`/`pessoa.observacao` são
tratados como atributo permanente da pessoa, mas o dado real é contextual a
UM atendimento — a mesma pessoa pode passar por hospitais diferentes em
estadias diferentes, e hoje cada nova estadia sobrescreve o hospital da
anterior (sem histórico). Mesmo raciocínio já aplicado a `pessoa.tipo` ->
`estadia.tipo_pessoa` (ver `pessoa.legacy.md`).

Levantamento no dump real (`abrigo_teste`, 2026-09-13): de 5.329 pessoas,
5.310 têm `id_hospital` preenchido e 5.001 têm `observacao` preenchida —
mas **2.541 dessas pessoas não têm nenhuma Estadia** (a maioria só tomou
empréstimo, algumas são acompanhantes sem leito próprio, outras sem vínculo
algum). Decisão do time: `Estadia` ganha `id_hospital` próprio (fonte de
verdade daqui pra frente, quando existe estadia), mas `Pessoa.id_hospital`/
`observacao` **não são removidos** — continuam servindo de fallback pra
quem nunca teve estadia.

Backfill (best-effort, não perde dado): pra cada pessoa com
`id_hospital`/`observacao` preenchidos, propaga pra sua estadia MAIS
RECENTE (`data_entrada` desc) — heurística razoável já que não dá pra saber
retroativamente qual estadia tinha aquele hospital/observação específicos.
`observacao` é concatenada (não sobrescrita) quando a estadia alvo já tem
texto próprio: `pessoa.observacao || '\n\n' || estadia.observacao`. Casos
com múltiplas estadias por pessoa (~832 no dump real) recebem o backfill só
na mais recente — as estadias mais antigas ficam sem hospital/observação
adicional, o que é aceitável (a suposição de que o dado antigo da pessoa se
aplicava a TODAS as estadias seria pior que não aplicar a nenhuma antiga).

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-13

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("estadia", sa.Column("id_hospital", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_estadia_hospital", "estadia", "hospital", ["id_hospital"], ["id_hospital"]
    )

    # Estadia mais recente de cada pessoa (heurística de qual estadia recebe
    # o backfill, ver docstring acima).
    op.execute(
        """
        WITH estadia_recente AS (
            SELECT DISTINCT ON (id_pessoa) id_estadia, id_pessoa
            FROM estadia
            ORDER BY id_pessoa, data_entrada DESC
        )
        UPDATE estadia e
        SET id_hospital = p.id_hospital
        FROM estadia_recente er
        JOIN pessoa p ON p.id_pessoa = er.id_pessoa
        WHERE e.id_estadia = er.id_estadia
          AND p.id_hospital IS NOT NULL
          AND e.id_hospital IS NULL
        """
    )

    op.execute(
        """
        WITH estadia_recente AS (
            SELECT DISTINCT ON (id_pessoa) id_estadia, id_pessoa
            FROM estadia
            ORDER BY id_pessoa, data_entrada DESC
        )
        UPDATE estadia e
        SET observacao = CASE
                WHEN e.observacao IS NULL OR trim(e.observacao) = '' THEN p.observacao
                ELSE p.observacao || E'\\n\\n' || e.observacao
            END
        FROM estadia_recente er
        JOIN pessoa p ON p.id_pessoa = er.id_pessoa
        WHERE e.id_estadia = er.id_estadia
          AND p.observacao IS NOT NULL AND trim(p.observacao) <> ''
        """
    )


def downgrade() -> None:
    # A concatenação de observacao não é reversível (não distinguimos o que
    # veio da pessoa do que já era da estadia) — mesmo padrão de não desfazer
    # dado adotado em 0018. Só remove a coluna nova.
    op.drop_constraint("fk_estadia_hospital", "estadia", type_="foreignkey")
    op.drop_column("estadia", "id_hospital")
