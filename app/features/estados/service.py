from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.estados.models import Estado


def listar(db: Session) -> list[Estado]:
    return list(db.scalars(select(Estado).order_by(Estado.nome)).all())


def buscar(db: Session, estado_id: int) -> Estado | None:
    return db.get(Estado, estado_id)
