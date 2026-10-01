from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Emprestimo(Base):
    """Mapeia a tabela `emprestimo` (schema confirmado no dump de produção
    `sgf_abrigo`, MySQL 5.5 — ver docs/migracao-postgres.md).

    `situacao` **não é digitada pelo usuário** — no legado é um
    `TcxDBTextEdit` com `Enabled = False`, recalculado automaticamente por
    `AtualizarSituacaoEmprestimo` (untFrmManutencaoEmprestimo.pas) a cada
    item criado/editado, com prioridade Renovado > Pendente > Devolvido
    (mesmas 3 constantes de `CasaApoio.Material.Constants.pas` usadas no
    combo do item). Ver `service._recalcular_situacao`. Mantido como
    `String` (não enum) na coluna porque é a mesma tabela usada pelo dado
    real migrado, mas o schema Pydantic (`SituacaoEmprestimo`) já valida o
    conjunto fechado. Dado real observado: 'Pendente', 'Devolvido' (nenhum
    'Renovado' no dump, mas o valor é possível pela lógica do legado).

    `data_emprestimo`/`data_devolucao`/`data_devolucao_efetiva` moveram do
    nível `EmprestimoItem` pra cá (migração `0029`, sem equivalente direto
    no legado, que guardava essas datas por item) — decisão do time: com
    itens de prazos distintos no mesmo empréstimo, o contrato de renovação
    (`_prazo_vigencia_contrato`) não batia corretamente (um item de 20 dias
    e outro de 40 dias no mesmo contrato). Um único prazo por empréstimo
    elimina a ambiguidade. `data_devolucao` continua **prevista**, digitada
    na criação/edição do empréstimo; `data_devolucao_efetiva` continua
    gravada automaticamente pelo backend quando `situacao` (calculada a
    partir dos itens) vira `'Devolvido'` — ver `service._recalcular_situacao`.
    """

    __tablename__ = "emprestimo"

    id: Mapped[int] = mapped_column("id_emprestimo", primary_key=True)
    id_pessoa: Mapped[int] = mapped_column(ForeignKey("pessoa.id_pessoa"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    situacao: Mapped[str] = mapped_column(String(60))
    numero_contrato: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_emprestimo: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_devolucao: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_devolucao_efetiva: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(default=True)


class EmprestimoItem(Base):
    """Mapeia a tabela `emprestimo_item` — cada material específico
    emprestado dentro de um `Emprestimo` (um empréstimo pode ter vários
    itens).

    `renovacao` é texto livre no legado (ex.: `'até 22/03/2019 até
    22/05/2019 Devolvido 02/07/2019'`) — não uma data ou boolean, mantido
    como `String`.

    As datas do aluguel (`data_emprestimo`/`data_devolucao`/
    `data_devolucao_efetiva`) moveram pra `Emprestimo` (migração `0029`) —
    ver docstring de `Emprestimo` acima. O item guarda só o material e a
    situação individual (usada pra calcular `Emprestimo.situacao`).
    """

    __tablename__ = "emprestimo_item"

    id: Mapped[int] = mapped_column("id_emprestimo_item", primary_key=True)
    id_emprestimo: Mapped[int] = mapped_column(ForeignKey("emprestimo.id_emprestimo"))
    id_material: Mapped[int] = mapped_column(ForeignKey("material.id_material"))
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


class EmprestimoContrato(Base):
    """Termo de responsabilidade assinado pela pessoa que toma o(s)
    material(is) emprestado(s) — feature nova (2026-09-13), sem equivalente
    no legado (que só guardava `Emprestimo.numero_contrato` como texto
    livre; o termo em si, se existia, era feito em papel fora do sistema —
    ver `emprestimo.legacy.md`).

    Um empréstimo pode ter vários contratos (`tipo` distingue qual é qual —
    ver `schemas.TipoContrato`): no máximo um "Comodato" (o termo original,
    assinado uma vez na criação do empréstimo) e quantos "Renovação"
    forem necessários (um termo aditivo a cada vez que o prazo é
    prorrogado — decisão do time, 2026-09-26, revertendo a regra anterior
    de "no máximo um contrato por empréstimo").

    `pdf` é o documento **assinado, congelado no momento da assinatura**
    (decisão do usuário: igual a um papel assinado, editar o empréstimo
    depois — ex. observação — não deve alterar o que já foi assinado). Por
    isso o service gera e guarda os bytes do PDF aqui, em vez de recriá-lo
    sob demanda a partir dos dados atuais do empréstimo. `assinatura` (PNG
    cru) também é guardada separada, à parte do PDF, só como registro
    auxiliar (não é exposta por nenhum endpoint hoje).
    """

    __tablename__ = "emprestimo_contrato"

    id: Mapped[int] = mapped_column("id_emprestimo_contrato", primary_key=True)
    id_emprestimo: Mapped[int] = mapped_column(ForeignKey("emprestimo.id_emprestimo"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    tipo: Mapped[str] = mapped_column(String(20), default="Comodato")
    assinatura: Mapped[bytes] = mapped_column(LargeBinary)
    pdf: Mapped[bytes] = mapped_column(LargeBinary)
    data_assinatura: Mapped[datetime] = mapped_column(DateTime)


class EmprestimoLinkAssinatura(Base):
    """Link de uso único pra a pessoa assinar o termo de comodato pelo
    próprio celular, sem login (2026-10-01, pedido do time) — só pra
    contratos pendentes, ou seja, empréstimos ainda sem "Comodato" assinado.

    O token em si nunca é guardado: só o hash SHA-256 (`token_hash`), como
    uma senha — quem tiver acesso ao banco não consegue montar o link. A
    pessoa precisa informar o CPF cadastrado pra abrir o termo; erros de CPF
    são contados (`tentativas_cpf`) e o link trava após
    `MAX_TENTATIVAS_CPF` (ver link_assinatura.py), porque CPF sozinho é um
    segredo fraco. Expira (`expira_em`), serve uma única vez (`usado_em`) e
    pode ser revogado (`revogado`) — gerar um link novo revoga os anteriores
    do empréstimo. `id_usuario` é quem gerou o link e consta como
    responsável no contrato assinado.
    """

    __tablename__ = "emprestimo_link_assinatura"

    id: Mapped[int] = mapped_column("id_emprestimo_link_assinatura", primary_key=True)
    id_emprestimo: Mapped[int] = mapped_column(ForeignKey("emprestimo.id_emprestimo"), index=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # Código curto (8 caracteres, ex.: K7M2-9PQX) que vale no lugar do token — pra
    # pessoa digitar na tela de login ("Assinar contrato") em vez de abrir o link.
    # Também só guardado como hash.
    codigo_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime)
    expira_em: Mapped[datetime] = mapped_column(DateTime)
    tentativas_cpf: Mapped[int] = mapped_column(default=0)
    usado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revogado: Mapped[bool] = mapped_column(default=False)
