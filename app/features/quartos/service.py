from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.quartos.models import Quarto
from app.features.quartos.schemas import QuartoCreate, QuartoUpdate


def listar(db: Session, apenas_ativos: bool = True) -> list[Quarto]:
    consulta = select(Quarto).order_by(Quarto.numero)
    if apenas_ativos:
        consulta = consulta.where(Quarto.ativo.is_(True))
    return list(db.scalars(consulta).all())


def buscar(db: Session, quarto_id: int) -> Quarto | None:
    return db.get(Quarto, quarto_id)


def criar(db: Session, dados: QuartoCreate) -> Quarto:
    quarto = Quarto(**dados.model_dump())
    db.add(quarto)
    db.commit()
    db.refresh(quarto)
    return quarto


def atualizar(db: Session, quarto: Quarto, dados: QuartoUpdate) -> Quarto:
    for campo, valor in dados.model_dump().items():
        setattr(quarto, campo, valor)
    db.commit()
    db.refresh(quarto)
    return quarto


def inativar(db: Session, quarto: Quarto) -> None:
    quarto.ativo = False
    db.commit()
