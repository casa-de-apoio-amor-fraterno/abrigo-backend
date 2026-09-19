"""Relatórios de listagem em PDF (Pessoas, Estadias, Materiais,
Empréstimos) — gerados sob demanda a partir do estado atual do banco (sem
persistência, diferente do contrato de empréstimo em
`app/features/emprestimos/service.py`, que é assinado e congelado)."""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.emprestimos.models import Emprestimo, EmprestimoItem
from app.features.estadias.models import Estadia, SituacaoEstadia, TipoPessoaEstadia
from app.features.estados.models import Estado
from app.features.hospitais.models import Hospital
from app.features.materiais.models import Material
from app.features.municipios.models import Municipio
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.relatorios.schemas import (
    FiltroSituacaoEmprestimo,
    FiltroSituacaoEstadia,
    PeriodoRelatorio,
    RelatorioResumoItem,
)
from app.shared.pdf import DocumentoPDF

_DIAS_POR_PERIODO: dict[PeriodoRelatorio, int] = {
    PeriodoRelatorio.SEMANAL: 7,
    PeriodoRelatorio.QUINZENAL: 15,
    PeriodoRelatorio.MENSAL: 30,
    PeriodoRelatorio.SEMESTRAL: 182,
    PeriodoRelatorio.ANUAL: 365,
}

_ROTULO_PERIODO: dict[PeriodoRelatorio, str] = {
    PeriodoRelatorio.SEMANAL: "última semana",
    PeriodoRelatorio.QUINZENAL: "últimos 15 dias",
    PeriodoRelatorio.MENSAL: "último mês",
    PeriodoRelatorio.SEMESTRAL: "últimos 6 meses",
    PeriodoRelatorio.ANUAL: "último ano",
}


def _data_limite(periodo: PeriodoRelatorio) -> date:
    return date.today() - timedelta(days=_DIAS_POR_PERIODO[periodo])


_ROTULO_SITUACAO_ESTADIA: dict[FiltroSituacaoEstadia, str] = {
    FiltroSituacaoEstadia.TODOS: "todas",
    FiltroSituacaoEstadia.EM_ACOMPANHAMENTO: "somente em acompanhamento",
}

_ROTULO_SITUACAO_EMPRESTIMO: dict[FiltroSituacaoEmprestimo, str] = {
    FiltroSituacaoEmprestimo.TODOS: "todos",
    FiltroSituacaoEmprestimo.ALUGADOS: "somente alugados",
    FiltroSituacaoEmprestimo.VENCIDOS: "somente vencidos",
}


def _criterios_situacao_estadia(situacao: FiltroSituacaoEstadia) -> tuple:
    if situacao is FiltroSituacaoEstadia.EM_ACOMPANHAMENTO:
        return (Estadia.situacao == SituacaoEstadia.EM_ACOMPANHAMENTO,)
    return ()


def _criterios_situacao_emprestimo(situacao: FiltroSituacaoEmprestimo) -> tuple:
    # "Alugados" = item ainda com o beneficiário (situação diferente de
    # "Devolvido"). "Vencidos" é um subconjunto disso: além de não
    # devolvido, a data de devolução prevista já passou.
    if situacao is FiltroSituacaoEmprestimo.ALUGADOS:
        return (EmprestimoItem.situacao != "Devolvido",)
    if situacao is FiltroSituacaoEmprestimo.VENCIDOS:
        return (
            EmprestimoItem.situacao != "Devolvido",
            EmprestimoItem.data_devolucao.is_not(None),
            EmprestimoItem.data_devolucao < date.today(),
        )
    return ()

# Mesmo rodapé institucional impresso nos relatórios do sistema legado (ver
# `relatorio_pessoas.pdf` etc. cedidos pela CAAF) — diferente do rodapé do
# contrato (`_RODAPE_CONTRATO` em `emprestimos/service.py`), que traz o
# endereço do Abrigo e do Bazar em vez do CNPJ da Matriz.
_RODAPE = [
    "Matriz - CNPJ 10.201.460/0001-31 Rua Dom Pedro II, n° 140, Cidade Nova, Porto União - SC",
    "E-mail: social@casaamorfraterno.org - Telefone (42) 3522 7765",
]


def _gerado_em() -> str:
    return f"Emitido em {datetime.now():%d/%m/%Y %H:%M}"


_TAMANHO_MAXIMO_OBSERVACAO = 220


def _truncar(texto: str | None, tamanho: int = _TAMANHO_MAXIMO_OBSERVACAO) -> str:
    """Corta textos livres longos (observação, motivo de baixa) antes de
    colocá-los numa célula da tabela — sem isso, um texto de várias linhas
    (comum no dado real migrado do legado) gera uma linha alta demais para
    caber numa única página, e o fpdf2 recusa a renderizar a tabela
    inteira (`ValueError: row ... too high`). O relatório é uma listagem
    resumida; o texto completo continua disponível na tela de detalhe."""
    texto = texto or "-"
    if len(texto) <= tamanho:
        return texto
    return texto[: tamanho - 1].rstrip() + "…"


def _mascarar_cpf(cpf: str | None) -> str:
    """Mascara o CPF pra exibição em relatório (LGPD - dado pessoal
    sensível não deve aparecer em texto claro num documento que pode ser
    impresso/compartilhado) — mantém só os 3 primeiros dígitos visíveis,
    ex. '081.***.***-28'. Números fora do padrão (11 dígitos) são
    mostrados como '-' em vez de arriscar expor um valor mal formatado."""
    digitos = "".join(c for c in (cpf or "") if c.isdigit())
    if len(digitos) != 11:
        return "-"
    return f"{digitos[:3]}.***.***-{digitos[9:]}"


def gerar_pdf_pessoas(db: Session, periodo: PeriodoRelatorio) -> bytes:
    consulta = select(Pessoa).where(Pessoa.ativo.is_(True), Pessoa.data_cadastro >= _data_limite(periodo))
    pessoas = list(db.scalars(consulta.order_by(Pessoa.nome)).all())
    estados = {estado.id: estado.uf for estado in db.scalars(select(Estado))}
    municipios = {municipio.id: municipio.nome for municipio in db.scalars(select(Municipio))}

    linhas = [
        [
            pessoa.nome,
            _mascarar_cpf(pessoa.cpf),
            pessoa.profissao or "-",
            pessoa.telefone_principal or "-",
            estados.get(pessoa.id_estado, "-") if pessoa.id_estado else "-",
            municipios.get(pessoa.id_municipio, "-") if pessoa.id_municipio else "-",
            _truncar(pessoa.observacao),
        ]
        for pessoa in pessoas
    ]

    pdf = DocumentoPDF(rodape=_RODAPE, orientation="L")
    pdf.titulo_documento(f"RELATÓRIO DE PESSOAS - Cadastros em: {_ROTULO_PERIODO[periodo]}\n{_gerado_em()}")
    pdf.tabela_relatorio(
        ["Nome", "CPF", "Profissão", "Telefone", "UF", "Município", "Observação"],
        linhas,
        larguras=[18, 10, 12, 12, 5, 13, 30],
    )
    pdf.totais([f"Total de pessoas: {len(pessoas)}"])
    return pdf.gerar_bytes()


def gerar_pdf_estadias(
    db: Session, periodo: PeriodoRelatorio, situacao: FiltroSituacaoEstadia = FiltroSituacaoEstadia.TODOS
) -> bytes:
    limite = datetime.combine(_data_limite(periodo), datetime.min.time())
    consulta = select(Estadia).where(Estadia.data_entrada >= limite, *_criterios_situacao_estadia(situacao))
    estadias = list(db.scalars(consulta.order_by(Estadia.data_entrada.desc())).all())
    pessoas = {pessoa.id: pessoa for pessoa in db.scalars(select(Pessoa))}
    estados = {estado.id: estado.uf for estado in db.scalars(select(Estado))}
    municipios = {municipio.id: municipio.nome for municipio in db.scalars(select(Municipio))}
    hospitais = {hospital.id: hospital.nome for hospital in db.scalars(select(Hospital))}
    quartos = {quarto.id: quarto.numero for quarto in db.scalars(select(Quarto))}

    linhas = []
    for estadia in estadias:
        pessoa = pessoas.get(estadia.id_pessoa)
        linhas.append(
            [
                str(estadia.id),
                f"{estadia.tipo_pessoa.value} - {pessoa.nome if pessoa else '-'}",
                (estados.get(pessoa.id_estado, "-") if pessoa and pessoa.id_estado else "-"),
                (municipios.get(pessoa.id_municipio, "-") if pessoa and pessoa.id_municipio else "-"),
                hospitais.get(estadia.id_hospital, "-") if estadia.id_hospital else "-",
                quartos.get(estadia.id_quarto, "-"),
                estadia.data_entrada.strftime("%d/%m/%Y"),
                estadia.data_saida.strftime("%d/%m/%Y") if estadia.data_saida else "-",
                estadia.situacao.value,
            ]
        )

    pdf = DocumentoPDF(rodape=_RODAPE, orientation="L")
    pdf.titulo_documento(
        f"RELATÓRIO DE ESTADIAS - Entradas em: {_ROTULO_PERIODO[periodo]} "
        f"({_ROTULO_SITUACAO_ESTADIA[situacao]})\n{_gerado_em()}"
    )
    pdf.tabela_relatorio(
        ["Código", "Tipo - Pessoa", "UF", "Município", "Hospital", "Quarto", "Entrada", "Saída", "Situação"],
        linhas,
        larguras=[7, 25, 5, 13, 15, 8, 10, 10, 12],
    )
    total_pacientes = sum(1 for e in estadias if e.tipo_pessoa == TipoPessoaEstadia.PACIENTE)
    total_acompanhantes = len(estadias) - total_pacientes
    pdf.totais(
        [
            f"Total de estadias: {len(estadias)}",
            f"Total de pacientes: {total_pacientes}",
            f"Total de acompanhantes: {total_acompanhantes}",
        ]
    )
    return pdf.gerar_bytes()


def gerar_pdf_materiais(db: Session) -> bytes:
    materiais = list(
        db.scalars(select(Material).where(Material.ativo.is_(True)).order_by(Material.descricao)).all()
    )

    linhas = [
        [
            str(material.id),
            material.codigo_identificacao or "-",
            material.descricao,
            material.local,
            material.situacao,
            "Sim" if material.disponivel_emprestimo else "Não",
            _truncar(material.motivo_baixa),
        ]
        for material in materiais
    ]

    pdf = DocumentoPDF(rodape=_RODAPE, orientation="L")
    pdf.titulo_documento(f"RELATÓRIO DE MATERIAIS\n{_gerado_em()}")
    pdf.tabela_relatorio(
        ["Cód.", "Cód. Identificação", "Descrição", "Local", "Situação", "Disp. Empréstimo", "Motivo baixa"],
        linhas,
        larguras=[8, 15, 30, 10, 12, 12, 23],
    )
    total_disponiveis = sum(1 for m in materiais if m.disponivel_emprestimo)
    total_baixados = sum(1 for m in materiais if m.situacao == "Baixado")
    pdf.totais(
        [
            f"Total de materiais: {len(materiais)}",
            f"Total disponíveis: {total_disponiveis}",
            f"Total baixados: {total_baixados}",
        ]
    )
    return pdf.gerar_bytes()


def gerar_pdf_emprestimos(
    db: Session, periodo: PeriodoRelatorio, situacao: FiltroSituacaoEmprestimo = FiltroSituacaoEmprestimo.TODOS
) -> bytes:
    limite = _data_limite(periodo)
    emprestimos = {
        emprestimo.id: emprestimo
        for emprestimo in db.scalars(select(Emprestimo).where(Emprestimo.ativo.is_(True)))
    }
    pessoas = {pessoa.id: pessoa for pessoa in db.scalars(select(Pessoa))}
    materiais = {material.id: material.descricao for material in db.scalars(select(Material))}

    # Filtra pelo item (data_emprestimo é do item, não do cabeçalho) — só
    # entram no relatório os itens cujo próprio empréstimo caiu dentro do
    # período escolhido, mesmo padrão de "Estadias" (filtra pela data do
    # evento, não pela data de criação do registro).
    itens_no_periodo = list(
        db.scalars(
            select(EmprestimoItem)
            .where(
                EmprestimoItem.data_emprestimo.is_not(None),
                EmprestimoItem.data_emprestimo >= limite,
                *_criterios_situacao_emprestimo(situacao),
            )
            .order_by(EmprestimoItem.data_emprestimo.desc())
        )
    )

    linhas = []
    for item in itens_no_periodo:
        emprestimo = emprestimos.get(item.id_emprestimo)
        if emprestimo is None:
            continue
        pessoa = pessoas.get(emprestimo.id_pessoa)
        linhas.append(
            [
                pessoa.nome if pessoa else "-",
                (pessoa.telefone_principal if pessoa else None) or "-",
                materiais.get(item.id_material, "-"),
                emprestimo.numero_contrato or "-",
                item.data_emprestimo.strftime("%d/%m/%Y") if item.data_emprestimo else "-",
                item.data_devolucao.strftime("%d/%m/%Y") if item.data_devolucao else "-",
                item.situacao or emprestimo.situacao,
            ]
        )

    pdf = DocumentoPDF(rodape=_RODAPE, orientation="L")
    pdf.titulo_documento(
        f"RELATÓRIO DE EMPRÉSTIMOS - Emprestados em: {_ROTULO_PERIODO[periodo]} "
        f"({_ROTULO_SITUACAO_EMPRESTIMO[situacao]})\n{_gerado_em()}"
    )
    pdf.tabela_relatorio(
        ["Beneficiário", "Telefone", "Item", "Nº Contrato", "Data empréstimo", "Data devolução", "Situação"],
        linhas,
        larguras=[22, 15, 20, 10, 12, 12, 9],
    )
    total_emprestimos = len({item.id_emprestimo for item in itens_no_periodo})
    pdf.totais(
        [
            f"Total de itens: {len(linhas)}",
            f"Total de empréstimos: {total_emprestimos}",
        ]
    )
    return pdf.gerar_bytes()


def resumo_pessoas(db: Session, periodo: PeriodoRelatorio) -> list[RelatorioResumoItem]:
    total_geral = db.scalar(select(func.count()).select_from(Pessoa).where(Pessoa.ativo.is_(True)))
    no_periodo = db.scalar(
        select(func.count())
        .select_from(Pessoa)
        .where(Pessoa.ativo.is_(True), Pessoa.data_cadastro >= _data_limite(periodo))
    )
    return [
        RelatorioResumoItem(
            rotulo=f"Novos cadastros ({_ROTULO_PERIODO[periodo]})", valor=str(no_periodo or 0)
        ),
        RelatorioResumoItem(rotulo="Total de pessoas cadastradas (geral)", valor=str(total_geral or 0)),
    ]


def resumo_estadias(
    db: Session, periodo: PeriodoRelatorio, situacao: FiltroSituacaoEstadia = FiltroSituacaoEstadia.TODOS
) -> list[RelatorioResumoItem]:
    limite = datetime.combine(_data_limite(periodo), datetime.min.time())
    criterios_situacao = _criterios_situacao_estadia(situacao)
    total_geral = db.scalar(select(func.count()).select_from(Estadia).where(*criterios_situacao))
    em_acompanhamento = db.scalar(
        select(func.count()).select_from(Estadia).where(Estadia.situacao == SituacaoEstadia.EM_ACOMPANHAMENTO)
    )
    no_periodo = db.scalar(
        select(func.count())
        .select_from(Estadia)
        .where(Estadia.data_entrada >= limite, *criterios_situacao)
    )
    return [
        RelatorioResumoItem(rotulo=f"Novas estadias ({_ROTULO_PERIODO[periodo]})", valor=str(no_periodo or 0)),
        RelatorioResumoItem(rotulo="Em acompanhamento (geral)", valor=str(em_acompanhamento or 0)),
        RelatorioResumoItem(rotulo="Total de estadias (geral)", valor=str(total_geral or 0)),
    ]


def resumo_materiais(db: Session) -> list[RelatorioResumoItem]:
    total = db.scalar(select(func.count()).select_from(Material).where(Material.ativo.is_(True)))
    disponiveis = db.scalar(
        select(func.count())
        .select_from(Material)
        .where(Material.ativo.is_(True), Material.disponivel_emprestimo.is_(True))
    )
    baixados = db.scalar(
        select(func.count()).select_from(Material).where(Material.ativo.is_(True), Material.situacao == "Baixado")
    )
    return [
        RelatorioResumoItem(rotulo="Total de materiais", valor=str(total or 0)),
        RelatorioResumoItem(rotulo="Disponíveis para empréstimo", valor=str(disponiveis or 0)),
        RelatorioResumoItem(rotulo="Baixados", valor=str(baixados or 0)),
    ]


def resumo_emprestimos(
    db: Session,
    periodo: PeriodoRelatorio,
    situacao: FiltroSituacaoEmprestimo = FiltroSituacaoEmprestimo.TODOS,
) -> list[RelatorioResumoItem]:
    limite = _data_limite(periodo)
    criterios_situacao = _criterios_situacao_emprestimo(situacao)
    itens_no_periodo = db.scalar(
        select(func.count())
        .select_from(EmprestimoItem)
        .where(
            EmprestimoItem.data_emprestimo.is_not(None),
            EmprestimoItem.data_emprestimo >= limite,
            *criterios_situacao,
        )
    )
    itens_vencidos = db.scalar(
        select(func.count())
        .select_from(EmprestimoItem)
        .where(*_criterios_situacao_emprestimo(FiltroSituacaoEmprestimo.VENCIDOS))
    )
    itens_em_aberto = db.scalar(
        select(func.count()).select_from(EmprestimoItem).where(EmprestimoItem.situacao != "Devolvido")
    )
    return [
        RelatorioResumoItem(
            rotulo=f"Itens emprestados ({_ROTULO_PERIODO[periodo]})", valor=str(itens_no_periodo or 0)
        ),
        RelatorioResumoItem(rotulo="Vencidos (geral)", valor=str(itens_vencidos or 0)),
        RelatorioResumoItem(rotulo="Itens emprestados no momento (geral)", valor=str(itens_em_aberto or 0)),
    ]
