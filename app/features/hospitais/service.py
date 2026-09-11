from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.hospitais.models import Hospital


def listar(db: Session, apenas_ativos: bool = True) -> list[Hospital]:
    consulta = select(Hospital).order_by(Hospital.nome)
    if apenas_ativos:
        consulta = consulta.where(Hospital.ativo.is_(True))
    return list(db.scalars(consulta).all())


def buscar(db: Session, hospital_id: int) -> Hospital | None:
    return db.get(Hospital, hospital_id)
