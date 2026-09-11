from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Voluntario(Base):
    """Mapeia a tabela `voluntario` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md)."""

    __tablename__ = "voluntario"

    id: Mapped[int] = mapped_column("id_voluntario", primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    setor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado_civil: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(60), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(60), nullable=True)
    formacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(default=True)

    contatos: Mapped[list["VoluntarioContato"]] = relationship(
        order_by="VoluntarioContato.id", cascade="all, delete-orphan"
    )

    @property
    def telefone_principal(self) -> str | None:
        """Ver `Pessoa.telefone_principal` — mesma normalização de telefone
        numa tabela própria, ver `pessoas/models.py` e
        `app/features/pessoas/pessoa.legacy.md` (seção Contatos)."""
        if not self.contatos:
            return None
        principal = next((c for c in self.contatos if c.principal), self.contatos[0])
        return principal.numero


class VoluntarioContato(Base):
    """Telefone(s) de contato de um voluntário — mesma normalização e
    mesmo motivo de `PessoaContato` (ver `app/features/pessoas/models.py`):
    `voluntario.telefone` legado era `varchar(60)` texto livre sem
    estrutura, dado real com formatos inconsistentes e às vezes mais de um
    número no mesmo campo."""

    __tablename__ = "voluntario_contato"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_voluntario: Mapped[int] = mapped_column(ForeignKey("voluntario.id_voluntario"))
    numero: Mapped[str] = mapped_column(String(60))
    nome_contato: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    principal: Mapped[bool] = mapped_column(default=False)
