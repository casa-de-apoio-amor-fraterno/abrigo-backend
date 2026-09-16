from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.emprestimos.models import (
    Emprestimo,
    EmprestimoContrato,
    EmprestimoHistorico,
    EmprestimoItem,
)
from app.features.emprestimos.schemas import (
    EmprestimoCreate,
    EmprestimoItemCreate,
    EmprestimoItemUpdate,
    EmprestimoUpdate,
)
from app.features.materiais.models import Material
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario
from app.shared.imagem import Base64Invalido, decodificar_base64_imagem
from app.shared.pdf import DocumentoPDF


def _registrar_historico(
    db: Session, id_emprestimo: int, id_usuario: int, tipo: str, observacao: str
) -> None:
    db.add(
        EmprestimoHistorico(
            id_emprestimo=id_emprestimo,
            id_usuario=id_usuario,
            tipo=tipo,
            observacao=observacao,
            # Coluna `DateTime` sem timezone (mesmo padrão de
            # `Estadia.data_entrada`) — grava naive em UTC.
            data_cadastro=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    db.commit()


def _recalcular_situacao(db: Session, emprestimo: Emprestimo) -> None:
    # `Emprestimo.situacao` não é digitada pelo usuário (campo read-only no
    # legado) — recalculada a cada item criado/editado, mesma lógica de
    # `AtualizarSituacaoEmprestimo` (untFrmManutencaoEmprestimo.pas):
    # qualquer item Renovado vence; senão qualquer item Pendente vence; só
    # vira Devolvido se todos os itens estiverem Devolvido; sem itens (ou
    # nenhuma situação reconhecida), default Pendente.
    itens = list(
        db.scalars(select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo.id)).all()
    )
    situacoes = {item.situacao for item in itens}
    if "Renovado" in situacoes:
        nova_situacao = "Renovado"
    elif "Pendente" in situacoes:
        nova_situacao = "Pendente"
    elif itens and all(item.situacao == "Devolvido" for item in itens):
        nova_situacao = "Devolvido"
    else:
        nova_situacao = "Pendente"

    if emprestimo.situacao != nova_situacao:
        emprestimo.situacao = nova_situacao
        db.commit()
        db.refresh(emprestimo)


def _aplicar_devolucao_efetiva(item: EmprestimoItem) -> None:
    # `data_devolucao` é prevista (digitada manualmente, ver models.py);
    # `data_devolucao_efetiva` é gravada aqui, automaticamente, só quando o
    # item passa a "Devolvido" — e limpa se a situação for corrigida pra
    # outra coisa depois.
    if item.situacao == "Devolvido":
        if item.data_devolucao_efetiva is None:
            item.data_devolucao_efetiva = date.today()
    else:
        item.data_devolucao_efetiva = None


def _descricao_item(db: Session, item: EmprestimoItem) -> str:
    material = db.get(Material, item.id_material)
    descricao_material = material.descricao if material else f"material #{item.id_material}"
    data_emprestimo = item.data_emprestimo.strftime("%d/%m/%Y") if item.data_emprestimo else "-"
    data_devolucao = item.data_devolucao.strftime("%d/%m/%Y") if item.data_devolucao else "-"
    data_devolucao_efetiva = (
        item.data_devolucao_efetiva.strftime("%d/%m/%Y") if item.data_devolucao_efetiva else "-"
    )
    return (
        f"{descricao_material} (situação: {item.situacao or '-'}, "
        f"data empréstimo: {data_emprestimo}, data devolução prevista: {data_devolucao}, "
        f"data devolução efetiva: {data_devolucao_efetiva})"
    )


def listar(
    db: Session,
    id_pessoa: int | None = None,
    situacao: str | None = None,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[Emprestimo], int]:
    consulta = select(Emprestimo).where(Emprestimo.ativo.is_(True))
    if id_pessoa is not None:
        consulta = consulta.where(Emprestimo.id_pessoa == id_pessoa)
    if situacao is not None:
        consulta = consulta.where(Emprestimo.situacao == situacao)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Emprestimo.id.desc()).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, emprestimo_id: int) -> Emprestimo | None:
    return db.get(Emprestimo, emprestimo_id)


def criar(db: Session, dados: EmprestimoCreate) -> Emprestimo:
    # Situação inicial do cabeçalho é sempre "Pendente" (mesmo default do
    # legado ao criar um novo registro, `btnNovoClick`) — recalculada logo
    # abaixo a partir dos itens aninhados, se houver algum.
    campos_emprestimo = dados.model_dump(exclude={"itens"})
    emprestimo = Emprestimo(**campos_emprestimo, situacao="Pendente")
    db.add(emprestimo)
    db.flush()  # gera emprestimo.id sem fechar a transação, pra usar como FK abaixo

    itens_criados = []
    for item_dados in dados.itens:
        item = EmprestimoItem(
            id_emprestimo=emprestimo.id, **item_dados.model_dump(exclude={"id_usuario"})
        )
        _aplicar_devolucao_efetiva(item)
        db.add(item)
        itens_criados.append((item, item_dados.id_usuario))

    db.commit()
    db.refresh(emprestimo)
    _recalcular_situacao(db, emprestimo)
    _registrar_historico(db, emprestimo.id, dados.id_usuario, "Inclusão", "Cadastro do registro.")

    for item, id_usuario_item in itens_criados:
        db.refresh(item)
        _registrar_historico(
            db,
            emprestimo.id,
            id_usuario_item,
            "Item incluído",
            f"Item incluído: {_descricao_item(db, item)}",
        )

    return emprestimo


def atualizar(db: Session, emprestimo: Emprestimo, dados: EmprestimoUpdate) -> Emprestimo:
    observacao_anterior = emprestimo.observacao or ""

    for campo, valor in dados.model_dump().items():
        setattr(emprestimo, campo, valor)
    db.commit()
    db.refresh(emprestimo)

    observacao_nova = emprestimo.observacao or ""
    if observacao_nova != observacao_anterior:
        # Observação normalmente cresce por acréscimo (usuário vai
        # completando o texto anterior) — nesse caso o histórico guarda só
        # o trecho novo, em vez de repetir tudo de novo a cada alteração.
        # Ver `qryDadosBeforePost` em `untDtmManutencaoEmprestimo.pas`.
        if observacao_nova.startswith(observacao_anterior):
            texto = observacao_nova[len(observacao_anterior):].strip()
        else:
            texto = f'Observação alterada de "{observacao_anterior}" para "{observacao_nova}"'

        if texto:
            _registrar_historico(db, emprestimo.id, dados.id_usuario, "Alteração", texto)

    return emprestimo


def inativar(db: Session, emprestimo: Emprestimo) -> None:
    emprestimo.ativo = False
    db.commit()


def _anexar_material(db: Session, itens: list[EmprestimoItem]) -> list[EmprestimoItem]:
    """Anexa `descricao_material`/`tem_foto_material` (atributos transientes,
    não persistidos em `emprestimo_item`) a cada item, pra popular
    `EmprestimoItemResponse` sem N+1 — usado pelo front pra mostrar a
    descrição e a miniatura do material no popover de devolução."""
    if not itens:
        return itens
    materiais = {
        m.id: m
        for m in db.scalars(
            select(Material).where(Material.id.in_({item.id_material for item in itens}))
        )
    }
    for item in itens:
        material = materiais.get(item.id_material)
        item.descricao_material = (  # type: ignore[attr-defined]
            material.descricao if material else f"material #{item.id_material}"
        )
        item.tem_foto_material = material.tem_foto if material else False  # type: ignore[attr-defined]
    return itens


def listar_itens(db: Session, emprestimo_id: int) -> list[EmprestimoItem]:
    consulta = select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo_id)
    itens = list(db.scalars(consulta.order_by(EmprestimoItem.id)).all())
    return _anexar_material(db, itens)


def adicionar_item(db: Session, emprestimo_id: int, dados: EmprestimoItemCreate) -> EmprestimoItem:
    item = EmprestimoItem(
        id_emprestimo=emprestimo_id, **dados.model_dump(exclude={"id_usuario"})
    )
    _aplicar_devolucao_efetiva(item)
    db.add(item)
    db.commit()
    db.refresh(item)
    emprestimo = db.get(Emprestimo, emprestimo_id)
    if emprestimo is not None:
        _recalcular_situacao(db, emprestimo)
    _registrar_historico(
        db, emprestimo_id, dados.id_usuario, "Item incluído", f"Item incluído: {_descricao_item(db, item)}"
    )
    _anexar_material(db, [item])
    return item


def buscar_item(db: Session, item_id: int) -> EmprestimoItem | None:
    return db.get(EmprestimoItem, item_id)


def atualizar_item(
    db: Session, item: EmprestimoItem, dados: EmprestimoItemUpdate
) -> EmprestimoItem:
    for campo, valor in dados.model_dump(exclude={"id_usuario"}).items():
        setattr(item, campo, valor)
    _aplicar_devolucao_efetiva(item)
    db.commit()
    db.refresh(item)
    emprestimo = db.get(Emprestimo, item.id_emprestimo)
    if emprestimo is not None:
        _recalcular_situacao(db, emprestimo)
    _registrar_historico(
        db, item.id_emprestimo, dados.id_usuario, "Item alterado", f"Item alterado: {_descricao_item(db, item)}"
    )
    _anexar_material(db, [item])
    return item


def devolver(
    db: Session, emprestimo: Emprestimo, id_usuario: int, data_devolucao: date | None = None
) -> Emprestimo:
    # Devolução em massa: marca o empréstimo e todos os itens ainda não
    # devolvidos como "Devolvido", e libera cada material associado — mesma
    # regra do legado (`AtualizarSituacaoMaterial` em
    # untDtmManutencaoEmprestimo.pas), que só não libera material já
    # "Baixado" (baixa é definitiva, não é desfeita por uma devolução).
    data_efetiva = data_devolucao or date.today()
    itens = list(
        db.scalars(select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo.id)).all()
    )

    itens_devolvidos = [item for item in itens if item.situacao != "Devolvido"]
    for item in itens_devolvidos:
        item.situacao = "Devolvido"
        item.data_devolucao_efetiva = data_efetiva

        material = db.get(Material, item.id_material)
        if material is not None and material.situacao != "Baixado":
            material.situacao = "Disponível"
            material.local = "Casa"
            material.disponivel_emprestimo = True

    db.commit()
    db.refresh(emprestimo)
    _recalcular_situacao(db, emprestimo)

    for item in itens_devolvidos:
        db.refresh(item)
        _registrar_historico(
            db, emprestimo.id, id_usuario, "Item alterado", f"Item alterado: {_descricao_item(db, item)}"
        )

    return emprestimo


def listar_historico(db: Session, emprestimo_id: int) -> list[EmprestimoHistorico]:
    consulta = select(EmprestimoHistorico).where(EmprestimoHistorico.id_emprestimo == emprestimo_id)
    return list(db.scalars(consulta.order_by(EmprestimoHistorico.data_cadastro.desc())).all())


class ContratoJaAssinado(Exception):
    pass


class ContratoDadosIncompletos(Exception):
    pass


TAMANHO_MAXIMO_ASSINATURA_BYTES = 2 * 1024 * 1024

# Texto do modelo real cedido pela CAAF (2026-09-16, "Contrato de Comodato
# de Bem Móvel - Empréstimo Solidário") — substitui o rascunho genérico
# anterior (ver git history / emprestimo.legacy.md). Cláusulas fixas
# (endereço/CNPJ da entidade, tabela de taxas, foro etc.) reproduzidas
# literalmente do modelo; só os campos abaixo são preenchidos por
# empréstimo: beneficiário, responsável (CPF/endereço/telefone), item(ns)
# emprestado(s) e prazo de vigência.
_RODAPE_CONTRATO = [
    "Abrigo: R. Dom Pedro II, 140, Cidade Nova - Porto União/SC. Tel.: (42) 3522-7765",
    "Bazar: R. Frei Rogério, 142, Centro - Porto União/SC. Tel.: (42) 3522-0322",
    "e-mail: contato@casaamorfraterno.org",
]

_TEXTO_INSTITUCIONAL = (
    "A Associação Família Zalewski - Casa de Apoio Amor Fraterno (CAAF) é uma instituição "
    "beneficente, sem fins lucrativos, mantida por doações e trabalho voluntário, que tem "
    "como finalidade oferecer acolhimento, hospedagem, alimentação e assistência a pacientes "
    "em tratamento de saúde e seus acompanhantes. Como forma de ampliar esse atendimento, a "
    "instituição mantém o Projeto Empréstimo Solidário, que disponibiliza gratuitamente "
    "equipamentos de apoio e recuperação, como cadeiras de rodas, andadores, muletas, camas "
    "hospitalares, bengalas e outros dispositivos auxiliares, contribuindo para a recuperação, "
    "mobilidade e qualidade de vida dos beneficiários que não possuem condições de adquiri-los."
)

_TEXTO_PARTES = (
    "Por este instrumento particular, de um lado Associação Família Zalewski - Casa de Apoio "
    "Amor Fraterno, com sede na cidade de Porto União, Estado de Santa Catarina, à Rua Dom "
    "Pedro II, nº 140, Cidade Nova, inscrita no CNPJ sob o nº 10.201.460/0001-31, neste ato "
    "representada por sua Presidente Laurete Dub Pinto Conte, doravante denominada simplesmente "
    "COMODANTE, e, de outro, **Responsável: {nome} CPF: {cpf} Endereço {endereco} Telefone "
    "{telefone}** Doravante denominado simplesmente de COMODATÁRIO, tem entre si como justo e "
    "acordado o que segue que se obrigam a cumprir por si e seus sucessores."
)

_CLAUSULA_1 = (
    "1. A Casa de Apoio Amor Fraterno (CAAF), na qualidade de legítima proprietária **de "
    "{itens}**, empresta ao comodatário gratuitamente, a título de comodato, em perfeito "
    "funcionamento, por meio do Projeto Empréstimo Solidário."
)

_CLAUSULA_2 = (
    "2. O PRAZO DE VIGÊNCIA deste contrato será de **{dias} DIAS**, com início em **{inicio}** "
    "e término em **{termino}**, data em que o __Responsável pelo Empréstimo__ deverá devolver o "
    "bem acima especificado nas mesmas condições em que recebeu, ou entrar em contato, "
    "solicitando a prorrogação do prazo. **O prazo máximo de empréstimo é de 6 (seis) meses.**"
)

_CLAUSULA_3 = (
    "**3. Só poderá ser realizada a renovação do Empréstimo se este estiver dentro do prazo de "
    "vigência, ou seja, caso o contrato esteja vencido, não será realizada a renovação do "
    "equipamento.**"
)

_CLAUSULA_4 = (
    "4. O **RESPONSÁVEL** pelo Empréstimo compromete-se a **ZELAR PELA CONSERVAÇÃO DO "
    "EQUIPAMENTO** recebido em comodato, utilizando-o de forma adequada e exclusivamente para "
    "sua finalidade. O equipamento será entregue após vistoria realizada pela CAAF, sendo "
    "registrado seu estado de conservação no momento do empréstimo. A devolução do equipamento "
    "ficará sujeita à nova vistoria da CAAF, que verificará suas condições de conservação e "
    "funcionamento na entrega do item, levando em consideração o desgaste de uso normal."
)

_TEXTO_DANOS = (
    "Por se tratar de equipamentos adquiridos e mantidos por meio de doações, o beneficiário "
    "compromete-se a utilizá-los com zelo e responsabilidade, preservando seu estado de "
    "conservação para que a instituição possa continuar atendendo outros usuários. O empréstimo "
    "é realizado GRATUITAMENTE, exceto se houver avarias. Caso o equipamento apresente danos "
    "decorrentes de mau uso, negligência, imprudência ou falta de conservação, o Responsável "
    "pelo Empréstimo deverá, a seu critério: I - providenciar o conserto do equipamento por "
    "profissional capacitado, devolvendo-o em perfeitas condições de uso e funcionamento, "
    "mediante aprovação da Casa de Apoio Amor Fraterno; ou II - efetuar o pagamento do valor "
    "correspondente ao reparo ou reposição do equipamento, conforme apresentado pela CAAF."
)

_CLAUSULA_5_INTRO = "5. Seguem os **valores de taxa de cada item**, caso haja constatação de avaria do equipamento:"

_TABELA_TAXAS = [
    ("Bota Ortopédica/Imobilizador/Colar/Colete/faixa", "R$ 40,00"),
    ("Colchão Pneumático", "R$ 50,00"),
    ("Muletas/Bengalas", "R$ 50,00"),
    ("Andador", "R$ 50,00"),
    ("Cadeira de Rodas", "R$ 150,00"),
    ("Cadeira de Banho", "R$ 130,00"),
    ("Cama Hospitalar", "R$ 400,00"),
    ("Concentrador de Oxigênio", "R$ 1000,00"),
    ("Cilindro c/ suporte", "R$ 500,00"),
]

_TEXTO_COLCHAO = (
    "(No processo de devolução, o colchão pneumático deverá permanecer conectado à tomada por "
    "24 horas para verificação de possíveis furos, vazamentos ou outros danos. Somente após "
    "essa inspeção e confirmação de que o equipamento está em condições adequadas será "
    "realizada a baixa no sistema.)"
)

_CLAUSULA_6 = (
    "6. Para os itens Concentrador de Oxigênio e Cilindro c/ suporte, a depender do dano no "
    "equipamento, poderá haver pena de realizar o pagamento do valor total atualizado do bem."
)
_CLAUSULA_7 = "7. O cilindro de oxigênio deve ser devolvido recarregado diretamente na CAAF."
_CLAUSULA_8 = (
    "8. O **Responsável pelo Empréstimo** deverá **DEVOLVER** o bem devidamente "
    "**HIGIENIZADO**, caso contrário deverá **PAGAR A TAXA** de R$ 40,00 para higienização do "
    "equipamento."
)
_CLAUSULA_9 = (
    "9. É vedado ao **Responsável pelo Empréstimo** sub-comodatar ou locar o equipamento "
    "emprestado a terceiros, bem como ceder ou transferir o presente contrato sem prévia "
    "autorização, por escrito, da Casa de Apoio Amor Fraterno."
)
_CLAUSULA_10 = (
    "10. As despesas com o **TRANSPORTE** do bem da sede da Casa de Apoio até a residência do "
    "beneficiário serão de inteira responsabilidade do **Responsável pelo Empréstimo**, tanto "
    "na retirada quanto na devolução."
)
_CLAUSULA_11 = (
    "11. Caso a CAAF necessite realizar a busca de qualquer equipamento emprestado, será "
    "cobrada taxa de transporte no valor de R$ 150,00, independentemente do tipo de "
    "equipamento. O valor destina-se a cobrir custos de combustível, veículo, motorista e "
    "demais despesas relacionadas ao deslocamento."
)
_CLAUSULA_12 = (
    "12. O presente instrumento será considerado rescindido de pleno direito em caso de "
    "infração, por parte do **Responsável pelo Empréstimo**, de qualquer cláusula acordada, "
    "assegurado à Casa de Apoio Amor Fraterno o direito de retirar, de onde quer que esteja, o "
    "bem ora cedido em comodato."
)
_CLAUSULA_13 = (
    "13. As partes elegem o foro da Comarca de Porto União, com exclusão de qualquer outro, por "
    "mais privilegiado que seja, para dirimir eventuais dúvidas ou litígios decorrentes deste "
    "contrato."
)

_TEXTO_ENCERRAMENTO = "E assim, por estarem justas e contratadas, as partes assinam o presente em duas vias de igual teor."
_TEXTO_DECLARACAO = (
    "**Declaro que recebi o equipamento descrito neste contrato em perfeitas condições de uso, "
    "funcionamento e conservação, comprometendo-me a devolvê-lo nas mesmas condições.**"
)

_MESES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho",
    7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def _data_por_extenso(data: date) -> str:
    return f"{data.day} de {_MESES_PT[data.month]} de {data.year}"


def _texto_itens_contrato(db: Session, itens: list[EmprestimoItem]) -> str:
    descricoes = []
    for item in itens:
        material = db.get(Material, item.id_material)
        nome = material.descricao.upper() if material else f"MATERIAL #{item.id_material}"
        codigo = material.codigo_identificacao if material else None
        descricoes.append(f"01 (UM) {nome} Nº {codigo}" if codigo else f"01 (UM) {nome}")
    if not descricoes:
        return "bem(ns) a ser(em) especificado(s)"
    return " e ".join(descricoes)


def _prazo_vigencia_contrato(itens: list[EmprestimoItem]) -> tuple[date, date, int]:
    datas_inicio = [item.data_emprestimo for item in itens if item.data_emprestimo]
    datas_termino = [item.data_devolucao for item in itens if item.data_devolucao]
    inicio = min(datas_inicio) if datas_inicio else date.today()
    termino = max(datas_termino) if datas_termino else inicio
    return inicio, termino, (termino - inicio).days


def _gerar_pdf_contrato(
    db: Session,
    emprestimo: Emprestimo,
    pessoa: Pessoa,
    usuario: Usuario,
    itens: list[EmprestimoItem],
    assinatura_png: bytes,
) -> bytes:
    identificador = emprestimo.numero_contrato or f"#{emprestimo.id}"
    inicio, termino, dias = _prazo_vigencia_contrato(itens)

    pdf = DocumentoPDF(rodape=_RODAPE_CONTRATO)
    pdf.titulo_documento(f"CONTRATO DE COMODATO DE BEM MÓVEL EMPRÉSTIMO SOLIDÁRIO\n{identificador}")

    pdf.paragrafo(f"IDENTIFICAÇÃO DO(A) BENEFICIÁRIO: **{pessoa.nome}**.")
    pdf.paragrafo(_TEXTO_INSTITUCIONAL)
    pdf.paragrafo(
        _TEXTO_PARTES.format(
            nome=pessoa.nome,
            cpf=pessoa.cpf or "-",
            endereco=pessoa.endereco or "-",
            telefone=pessoa.telefone_principal or "-",
        )
    )

    pdf.paragrafo(_CLAUSULA_1.format(itens=_texto_itens_contrato(db, itens)))
    pdf.paragrafo(
        _CLAUSULA_2.format(
            dias=dias, inicio=inicio.strftime("%d/%m/%Y"), termino=termino.strftime("%d/%m/%Y")
        )
    )
    pdf.paragrafo(_CLAUSULA_3)
    pdf.paragrafo(_CLAUSULA_4)
    pdf.paragrafo(_TEXTO_DANOS)
    pdf.paragrafo(_CLAUSULA_5_INTRO)
    pdf.tabela(["ITEM/EQUIPAMENTO", "VALOR"], [list(linha) for linha in _TABELA_TAXAS])
    pdf.paragrafo(_TEXTO_COLCHAO)
    pdf.paragrafo(_CLAUSULA_6)
    pdf.paragrafo(_CLAUSULA_7)
    pdf.paragrafo(_CLAUSULA_8)
    pdf.paragrafo(_CLAUSULA_9)
    pdf.paragrafo(_CLAUSULA_10)
    pdf.paragrafo(_CLAUSULA_11)
    pdf.paragrafo(_CLAUSULA_12)
    pdf.paragrafo(_CLAUSULA_13)
    pdf.paragrafo(_TEXTO_ENCERRAMENTO)
    pdf.paragrafo(_TEXTO_DECLARACAO)
    pdf.paragrafo(f"Porto União, {_data_por_extenso(date.today())}.")

    pdf.campo_assinatura(f"{pessoa.nome} - Responsável pelo Empréstimo", imagem_assinatura=assinatura_png)
    pdf.assinaturas_lado_a_lado(
        [("Laurete Dub Pinto Conte", "Presidente"), ("Cinthia Keiser", "Gerente Geral")]
    )

    return pdf.gerar_bytes()


def buscar_contrato(db: Session, emprestimo_id: int) -> EmprestimoContrato | None:
    return db.scalar(
        select(EmprestimoContrato).where(EmprestimoContrato.id_emprestimo == emprestimo_id)
    )


def criar_contrato(
    db: Session, emprestimo: Emprestimo, id_usuario: int, assinatura_png_base64: str
) -> EmprestimoContrato:
    if buscar_contrato(db, emprestimo.id) is not None:
        raise ContratoJaAssinado("Este empréstimo já tem um contrato assinado.")

    assinatura_png = decodificar_base64_imagem(assinatura_png_base64)
    if len(assinatura_png) > TAMANHO_MAXIMO_ASSINATURA_BYTES:
        raise Base64Invalido("Assinatura maior que o limite permitido (2MB).")

    pessoa = db.get(Pessoa, emprestimo.id_pessoa)
    usuario = db.get(Usuario, id_usuario)
    if pessoa is None or usuario is None:
        raise ContratoDadosIncompletos("Pessoa ou usuário do empréstimo não encontrado.")

    itens = list(
        db.scalars(select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo.id)).all()
    )
    pdf_bytes = _gerar_pdf_contrato(db, emprestimo, pessoa, usuario, itens, assinatura_png)

    contrato = EmprestimoContrato(
        id_emprestimo=emprestimo.id,
        id_usuario=id_usuario,
        assinatura=assinatura_png,
        pdf=pdf_bytes,
        data_assinatura=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(contrato)
    db.commit()
    db.refresh(contrato)

    _registrar_historico(
        db, emprestimo.id, id_usuario, "Contrato assinado", "Termo de responsabilidade assinado."
    )

    return contrato
