import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TipoPessoaEstadia(str, enum.Enum):
    """Papel da pessoa *nesta* estadia (nesta ocupação de quarto/leito) —
    contextual ao evento, não um atributo permanente da pessoa (ver
    `app/features/pessoas/pessoa.legacy.md`)."""

    PACIENTE = "Paciente"
    ACOMPANHANTE = "Acompanhante"


class SituacaoEstadia(str, enum.Enum):
    EM_ACOMPANHAMENTO = "Em acompanhamento"
    AGUARDANDO_RETORNO = "Aguardando retorno"
    FINALIZADA = "Finalizada"


class UnidadeTempoEstadia(str, enum.Enum):
    """Unidade do novo par estruturado `tempo_estadia_valor` /
    `tempo_estadia_unidade` (ver decisão em `estadia.legacy.md`, migração
    0017)."""

    DIAS = "dias"
    NOITES = "noites"
    HORAS = "horas"


class Estadia(Base):
    """Mapeia a tabela `estadia` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `tipo_pessoa` **não é redundante** com `EstadiaAcompanhante` (achado 3
    de `docs/atividades.md`, resolvido — ver `estadia.legacy.md`): uma
    `Estadia` sempre representa a ocupação de um `quarto`/leito por UMA
    pessoa, e `tipo_pessoa` diz se essa pessoa está ali como paciente ou
    como acompanhante que também ocupa leito próprio. `EstadiaAcompanhante`
    é um conceito diferente — pessoas que acompanham a estadia de um
    paciente sem necessariamente ter leito próprio, com sua própria janela
    de entrada/saída e grau de parentesco.

    `tempo_estadia` é texto livre legado (ex.: "06 dias ", "4 dias") —
    **DEPRECATED** (migração 0017): mantido apenas para auditoria/histórico
    dos casos que não deu pra migrar automaticamente (grafia irregular,
    texto usado como observação etc. — ver `estadia.legacy.md`). Não
    editável mais pelo frontend. Para dado estruturado, usar
    `tempo_estadia_valor` + `tempo_estadia_unidade`, preenchidos por uma
    migração de dados a partir do texto legado quando o formato era
    reconhecível ("N dias/noite(s)/hora(s)"), daqui pra frente preenchidos
    diretamente pelo formulário.
    """

    __tablename__ = "estadia"

    id: Mapped[int] = mapped_column("id_estadia", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    id_quarto: Mapped[int] = mapped_column(ForeignKey("quarto.id_quarto"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    data_entrada: Mapped[datetime] = mapped_column(DateTime)
    data_saida: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tempo_estadia: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tempo_estadia_valor: Mapped[int | None] = mapped_column(nullable=True)
    tempo_estadia_unidade: Mapped[UnidadeTempoEstadia | None] = mapped_column(
        Enum(
            UnidadeTempoEstadia,
            native_enum=False,
            length=10,
            # Sem values_callable, o SQLAlchemy grava o *nome* do membro
            # ("DIAS") em vez do `.value` ("dias") — inconsistente com o
            # texto gravado pela migração 0017/ETL (via SQL cru, usa o
            # valor). Mesmo padrão aplicado em `situacao` e `tipo_pessoa`
            # abaixo (migração de dados de correção em 0018).
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        nullable=True,
    )
    tipo_pessoa: Mapped[TipoPessoaEstadia] = mapped_column(
        Enum(
            TipoPessoaEstadia,
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        ),
        default=TipoPessoaEstadia.PACIENTE,
    )
    situacao: Mapped[SituacaoEstadia] = mapped_column(
        Enum(
            SituacaoEstadia,
            native_enum=False,
            length=30,
            values_callable=lambda enum_cls: [membro.value for membro in enum_cls],
        )
    )
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool | None] = mapped_column(nullable=True, default=True)


class EstadiaAcompanhante(Base):
    """Mapeia a tabela `estadia_acompanhante` — pessoas que acompanham a
    estadia de um paciente, com sua própria janela de entrada/saída e grau
    de parentesco. Ver decisão em `estadia.legacy.md` (achado 3)."""

    __tablename__ = "estadia_acompanhante"

    id: Mapped[int] = mapped_column("id_estadia_acompanhante", primary_key=True)
    id_estadia: Mapped[int] = mapped_column(ForeignKey("estadia.id_estadia"))
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    data_entrada: Mapped[datetime] = mapped_column(DateTime)
    data_saida: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    grau_parentesco: Mapped[str | None] = mapped_column(String(100), nullable=True)
