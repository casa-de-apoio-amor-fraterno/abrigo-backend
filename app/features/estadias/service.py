from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.estadias.models import Estadia, EstadiaAcompanhante, SituacaoEstadia
from app.features.estadias.schemas import (
    EstadiaAcompanhanteCreate,
    EstadiaCreate,
    EstadiaUpdate,
)


def listar(
    db: Session,
    id_pessoa: int | None = None,
    situacao: SituacaoEstadia | None = None,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[Estadia], int]:
    consulta = select(Estadia)
    if id_pessoa is not None:
        consulta = consulta.where(Estadia.id_pessoa == id_pessoa)
    if situacao is not None:
        consulta = consulta.where(Estadia.situacao == situacao)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(
        consulta.order_by(Estadia.data_entrada.desc()).offset(skip).limit(take)
    ).all()
    return list(itens), total


def buscar(db: Session, estadia_id: int) -> Estadia | None:
    return db.get(Estadia, estadia_id)


def criar(db: Session, dados: EstadiaCreate) -> Estadia:
    estadia = Estadia(**dados.model_dump())
    db.add(estadia)
    db.commit()
    db.refresh(estadia)
    return estadia


def atualizar(db: Session, estadia: Estadia, dados: EstadiaUpdate) -> Estadia:
    for campo, valor in dados.model_dump().items():
        setattr(estadia, campo, valor)
    db.commit()
    db.refresh(estadia)
    return estadia


def encerrar(db: Session, estadia: Estadia, data_saida: datetime | None = None) -> Estadia:
    estadia.situacao = SituacaoEstadia.FINALIZADA
    estadia.data_saida = data_saida or datetime.now(UTC).replace(tzinfo=None)
    estadia.ativo = False
    db.commit()
    db.refresh(estadia)
    return estadia


def listar_acompanhantes(db: Session, estadia_id: int) -> list[EstadiaAcompanhante]:
    consulta = select(EstadiaAcompanhante).where(EstadiaAcompanhante.id_estadia == estadia_id)
    return list(db.scalars(consulta.order_by(EstadiaAcompanhante.data_entrada)).all())


def adicionar_acompanhante(
    db: Session, estadia_id: int, dados: EstadiaAcompanhanteCreate
) -> EstadiaAcompanhante:
    acompanhante = EstadiaAcompanhante(id_estadia=estadia_id, **dados.model_dump())
    db.add(acompanhante)
    db.commit()
    db.refresh(acompanhante)
    return acompanhante
