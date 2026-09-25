import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GrauParentesco(str, enum.Enum):
    """Lista fechada de graus de parentesco — antes era texto livre
    (varchar(60)), com ~90 variações reais no dump de produção (case
    inconsistente, erros de digitação, placeholders como "----" e valores
    que não são parentesco, ex. "vizinho"/"casada"). Migração 0023 faz o
    backfill dos dados existentes pra essa lista; o que não bate com
    nenhuma variação conhecida cai em `OUTRO`."""

    PAI = "Pai"
    MAE = "Mãe"
    FILHO = "Filho"
    FILHA = "Filha"
    ESPOSO = "Esposo"
    ESPOSA = "Esposa"
    COMPANHEIRO = "Companheiro"
    COMPANHEIRA = "Companheira"
    NAMORADO = "Namorado"
    NAMORADA = "Namorada"
    IRMAO = "Irmão"
    IRMA = "Irmã"
    AVO = "Avô"
    AVOA = "Avó"
    BISAVO = "Bisavô"
    BISAVOA = "Bisavó"
    NETO = "Neto"
    NETA = "Neta"
    BISNETO = "Bisneto"
    BISNETA = "Bisneta"
    GENRO = "Genro"
    NORA = "Nora"
    SOGRO = "Sogro"
    SOGRA = "Sogra"
    CUNHADO = "Cunhado"
    CUNHADA = "Cunhada"
    TIO = "Tio"
    TIA = "Tia"
    SOBRINHO = "Sobrinho"
    SOBRINHA = "Sobrinha"
    PRIMO = "Primo"
    PRIMA = "Prima"
    ENTEADO = "Enteado"
    ENTEADA = "Enteada"
    PADRASTO = "Padrasto"
    MADRASTA = "Madrasta"
    CUIDADOR = "Cuidador"
    CUIDADORA = "Cuidadora"
    RESPONSAVEL = "Responsável"
    OUTRO = "Outro"


class ComposicaoFamiliar(Base):
    """Mapeia a tabela `composicao_familiar` (schema confirmado no dump de
    produção `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    Sub-rotina de `Pessoa`, mesma regra de acesso restrito de
    `avaliacao_social` (ver `composicao_familiar.legacy.md`).

    `idade` é `varchar(60)`, não `int` — dado real pode ter valores como
    "5 meses", não só anos completos; mantido como `String`.

    `grau_parentesco` era texto livre — convertido pra `GrauParentesco`
    (migração 0023, ver docstring lá pro mapeamento completo dos dados
    legados).
    """

    __tablename__ = "composicao_familiar"

    id: Mapped[int] = mapped_column("id_composicao_familiar", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    nome: Mapped[str] = mapped_column(String(60))
    idade: Mapped[str | None] = mapped_column(String(60), nullable=True)
    grau_parentesco: Mapped[GrauParentesco] = mapped_column(
        Enum(
            GrauParentesco,
            native_enum=False,
            length=60,
            # Sem values_callable, o SQLAlchemy grava o *nome* do membro
            # ("ESPOSO") em vez do `.value` ("Esposo") — mesmo bug já
            # corrigido em estadias/models.py (migração 0018).
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        )
    )
    estado_civil: Mapped[str | None] = mapped_column(String(60), nullable=True)
    renda: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ocupacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
