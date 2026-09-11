from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.composicao_familiar.models import ComposicaoFamiliar
from app.features.composicao_familiar.schemas import (
    ComposicaoFamiliarCreate,
    ComposicaoFamiliarUpdate,
)


def listar_por_pessoa(db: Session, pessoa_id: int) -> list[ComposicaoFamiliar]:
    consulta = select(ComposicaoFamiliar).where(ComposicaoFamiliar.id_pessoa == pessoa_id)
    return list(db.scalars(consulta.order_by(ComposicaoFamiliar.nome)).all())


def buscar(db: Session, membro_id: int) -> ComposicaoFamiliar | None:
    return db.get(ComposicaoFamiliar, membro_id)


def criar(db: Session, pessoa_id: int, dados: ComposicaoFamiliarCreate) -> ComposicaoFamiliar:
    membro = ComposicaoFamiliar(id_pessoa=pessoa_id, **dados.model_dump())
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return membro


def atualizar(
    db: Session, membro: ComposicaoFamiliar, dados: ComposicaoFamiliarUpdate
) -> ComposicaoFamiliar:
    for campo, valor in dados.model_dump().items():
        setattr(membro, campo, valor)
    db.commit()
    db.refresh(membro)
    return membro


def remover(db: Session, membro: ComposicaoFamiliar) -> None:
    db.delete(membro)
    db.commit()
