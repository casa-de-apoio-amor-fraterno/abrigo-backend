"""Corrige enums gravados pelo nome do membro em vez do valor

Bug: colunas `Enum(..., native_enum=False)` sem `values_callable` fazem o
SQLAlchemy ORM gravar o *nome* do membro Python (ex.: "EM_ACOMPANHAMENTO")
em vez do `.value` ("Em acompanhamento") em todo INSERT/UPDATE feito via
ORM — só fica certo quando o dado chega via SQL cru, como a ETL de
migração do legado. Isso não aparece no round-trip da API (o SQLAlchemy
decodifica de volta pelo mesmo nome), mas quebra filtros/relatórios que
comparam com o valor certo (ex.: os ~4400 registros migrados do legado) e
qualquer consulta SQL direta no banco. Corrigido na origem em
`app/features/estadias/models.py` e
`app/features/solicitacoes_cadastro/models.py` com `values_callable`;
esta migração corrige as linhas já gravadas erradas.

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-12

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

# (tabela, coluna): [(nome_do_membro, valor), ...]
_CORRECOES = {
    ("estadia", "situacao"): [
        ("EM_ACOMPANHAMENTO", "Em acompanhamento"),
        ("AGUARDANDO_RETORNO", "Aguardando retorno"),
        ("FINALIZADA", "Finalizada"),
    ],
    ("estadia", "tipo_pessoa"): [
        ("PACIENTE", "Paciente"),
        ("ACOMPANHANTE", "Acompanhante"),
    ],
    ("solicitacao_cadastro_paciente", "situacao"): [
        ("PENDENTE", "Pendente"),
        ("APROVADA", "Aprovada"),
        ("REVOGADA", "Revogada"),
    ],
}


def upgrade() -> None:
    for (tabela, coluna), pares in _CORRECOES.items():
        for nome, valor in pares:
            op.execute(
                sa.text(f"UPDATE {tabela} SET {coluna} = :valor WHERE {coluna} = :nome").bindparams(
                    valor=valor, nome=nome
                )
            )


def downgrade() -> None:
    # Irreversível por natureza (não distinguimos linhas gravadas certas
    # via ETL das corrigidas por esta migração) — não desfaz.
    pass
