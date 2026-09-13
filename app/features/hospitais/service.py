from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.hospitais.models import Hospital
from app.features.hospitais.schemas import HospitalCreate, HospitalUpdate


def listar(db: Session, apenas_ativos: bool = True) -> list[Hospital]:
    consulta = select(Hospital).order_by(Hospital.nome)
    if apenas_ativos:
        consulta = consulta.where(Hospital.ativo.is_(True))
    return list(db.scalars(consulta).all())


def buscar(db: Session, hospital_id: int) -> Hospital | None:
    return db.get(Hospital, hospital_id)


def criar(db: Session, dados: HospitalCreate) -> Hospital:
    hospital = Hospital(**dados.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


def atualizar(db: Session, hospital: Hospital, dados: HospitalUpdate) -> Hospital:
    for campo, valor in dados.model_dump().items():
        setattr(hospital, campo, valor)
    db.commit()
    db.refresh(hospital)
    return hospital


def inativar(db: Session, hospital: Hospital) -> None:
    hospital.ativo = False
    db.commit()
