from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Emprestimo(Base):
    """Mapeia a tabela `emprestimo` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `situacao` é campo de texto livre no legado (`TStringField` sem combo
    fechado, mesmo padrão de `material.situacao`) — mantido como `String`,
    não enum. Dado real observado: 'Pendente', 'Devolvido'.
    """

    __tablename__ = "emprestimo"

    id: Mapped[int] = mapped_column("id_emprestimo", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    situacao: Mapped[str] = mapped_column(String(60))
    numero_contrato: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(default=True)


class EmprestimoItem(Base):
    """Mapeia a tabela `emprestimo_item` — cada material específico
    emprestado dentro de um `Emprestimo` (um empréstimo pode ter vários
    itens).

    `renovacao` é texto livre no legado (ex.: `'até 22/03/2019 até
    22/05/2019 Devolvido 02/07/2019'`) — não uma data ou boolean, mantido
    como `String`.
    """

    __tablename__ = "emprestimo_item"

    id: Mapped[int] = mapped_column("id_emprestimo_item", primary_key=True)
    id_emprestimo: Mapped[int] = mapped_column(ForeignKey("emprestimo.id_emprestimo"))
    id_material: Mapped[int] = mapped_column(ForeignKey("material.id_material"))
    data_emprestimo: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_devolucao: Mapped[date | None] = mapped_column(Date, nullable=True)
    situacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    renovacao: Mapped[str | None] = mapped_column(String(60), nullable=True)


class EmprestimoHistorico(Base):
    """Mapeia a tabela `emprestimo_historico` — trilha de auditoria criada
    pelo legado em 2026-09-09 (`Scripts/Atualização Setembro 2026/Criar
    tabela emprestimo_historico.sql`), ainda não presente no dump de
    produção usado na migração inicial. Registrada automaticamente pelo
    backend (nunca por escrita direta do cliente) a cada criação de
    empréstimo, alteração de observação, ou inclusão/edição de item — ver
    `service.py` (`_registrar_historico`) e a lógica original em
    `untDtmManutencaoEmprestimo.pas` (`RegistrarHistorico`,
    `qryDadosBeforePost`, `SalvarDetalhe`).

    `tipo` é texto livre no legado (varchar(20)) com valores observados:
    'Inclusão', 'Alteração', 'Item incluído', 'Item alterado' — mantido
    como `String`, não enum.
    """

    __tablename__ = "emprestimo_historico"

    id: Mapped[int] = mapped_column("id_emprestimo_historico", primary_key=True)
    id_emprestimo: Mapped[int] = mapped_column(ForeignKey("emprestimo.id_emprestimo"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    tipo: Mapped[str] = mapped_column(String(20))
    observacao: Mapped[str] = mapped_column(Text)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime)
