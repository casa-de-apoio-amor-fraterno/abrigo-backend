from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.emprestimos.models import Emprestimo, EmprestimoHistorico, EmprestimoItem
from app.features.emprestimos.schemas import (
    EmprestimoCreate,
    EmprestimoItemCreate,
    EmprestimoItemUpdate,
    EmprestimoUpdate,
)
from app.features.materiais.models import Material


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


def listar_itens(db: Session, emprestimo_id: int) -> list[EmprestimoItem]:
    consulta = select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo_id)
    return list(db.scalars(consulta.order_by(EmprestimoItem.id)).all())


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
