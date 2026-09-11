from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.emprestimos.models import Emprestimo, EmprestimoItem
from app.features.emprestimos.schemas import (
    EmprestimoCreate,
    EmprestimoItemCreate,
    EmprestimoItemUpdate,
    EmprestimoUpdate,
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
    emprestimo = Emprestimo(**dados.model_dump())
    db.add(emprestimo)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


def atualizar(db: Session, emprestimo: Emprestimo, dados: EmprestimoUpdate) -> Emprestimo:
    for campo, valor in dados.model_dump().items():
        setattr(emprestimo, campo, valor)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


def inativar(db: Session, emprestimo: Emprestimo) -> None:
    emprestimo.ativo = False
    db.commit()


def listar_itens(db: Session, emprestimo_id: int) -> list[EmprestimoItem]:
    consulta = select(EmprestimoItem).where(EmprestimoItem.id_emprestimo == emprestimo_id)
    return list(db.scalars(consulta.order_by(EmprestimoItem.id)).all())


def adicionar_item(db: Session, emprestimo_id: int, dados: EmprestimoItemCreate) -> EmprestimoItem:
    item = EmprestimoItem(id_emprestimo=emprestimo_id, **dados.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def buscar_item(db: Session, item_id: int) -> EmprestimoItem | None:
    return db.get(EmprestimoItem, item_id)


def atualizar_item(
    db: Session, item: EmprestimoItem, dados: EmprestimoItemUpdate
) -> EmprestimoItem:
    for campo, valor in dados.model_dump().items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item
