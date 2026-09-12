import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SituacaoSolicitacaoCadastro(str, enum.Enum):
    PENDENTE = "Pendente"
    APROVADA = "Aprovada"
    REVOGADA = "Revogada"


class SolicitacaoCadastroPaciente(Base):
    """Feature nova (2026-09-12), sem equivalente no legado — auto-cadastro
    público de paciente pelo próprio celular (tela de login, opção "Sou
    paciente"). Fica `Pendente` até um usuário do sistema aprovar ou
    revogar: como a criação (`POST /solicitacoes-cadastro`) é pública, sem
    login, esse registro fica separado de `Pessoa` até ser confirmado — só
    vira uma `Pessoa` de verdade em `service.aprovar`, evitando dado não
    confirmado (ou spam) direto na base real de pessoas atendidas.
    """

    __tablename__ = "solicitacao_cadastro_paciente"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    data_nascimento: Mapped[date] = mapped_column(Date)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    foto: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    foto_content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    situacao: Mapped[SituacaoSolicitacaoCadastro] = mapped_column(
        Enum(SituacaoSolicitacaoCadastro, native_enum=False, length=20),
        default=SituacaoSolicitacaoCadastro.PENDENTE,
    )
    data_solicitacao: Mapped[datetime] = mapped_column(DateTime)
    # Preenchido só em `aprovar` — a Pessoa criada a partir desta solicitação.
    id_pessoa: Mapped[int | None] = mapped_column(ForeignKey("pessoa.id_pessoa"), nullable=True)
    # Quem aprovou/revogou e quando — trilha mínima de auditoria, já que é
    # uma decisão sobre um cadastro que ninguém da equipe digitou.
    id_usuario_analise: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id_usuario"), nullable=True
    )
    data_analise: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def tem_foto(self) -> bool:
        return self.foto is not None
