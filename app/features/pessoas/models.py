from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Pessoa(Base):
    """Mapeia a tabela `pessoa` já existente em produção (sistema legado, desde 2013).

    Não inclui o campo legado `tipo` (Paciente/Acompanhante/Emprestimo) — ver
    `pessoa.legacy.md`: é um papel contextual de uma estadia, não um atributo
    permanente da pessoa, e deve ser modelado em `Estadia.tipo_pessoa` (ou na
    entidade de empréstimo), não aqui.

    `id_hospital`, `id_municipio` e `id_estado` ficam como IDs simples por
    enquanto — viram chave estrangeira de verdade quando essas tabelas forem
    mapeadas (features `hospitais`, `municipios`, `estados`).
    """

    __tablename__ = "pessoa"

    id: Mapped[int] = mapped_column("id_pessoa", primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    rg: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    profissao: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cartao_sus: Mapped[str | None] = mapped_column(String(20), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ponto_referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_hospital: Mapped[int | None] = mapped_column(nullable=True)
    id_municipio: Mapped[int | None] = mapped_column(nullable=True)
    id_estado: Mapped[int | None] = mapped_column(nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    acompanhamento_social: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_cadastro: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
