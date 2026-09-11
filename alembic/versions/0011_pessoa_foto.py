"""Adiciona foto de Pessoa

Feature nova (2026-09-11) — o legado (`untFrmManutencaoPessoa.pas`)
capturava a foto pela webcam (componente DevExpress `TdxCameraControl`) e
salvava como arquivo `.bmp` em disco (`pessoas\\<id_pessoa>.bmp`), sem
coluna correspondente na tabela `pessoa`. Não há dado real pra migrar — os
arquivos ficavam na máquina onde o Delphi rodava, fora do dump de produção
e do controle de versão. Aqui vira BLOB (`bytea`) no próprio Postgres, sem
exigir storage externo. Ver `app/features/pessoas/pessoa.legacy.md`.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-11

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pessoa", sa.Column("foto", sa.LargeBinary(), nullable=True))
    op.add_column("pessoa", sa.Column("foto_content_type", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("pessoa", "foto_content_type")
    op.drop_column("pessoa", "foto")
