from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.materiais_locais.models import MaterialLocal
from app.features.materiais_locais.schemas import MaterialLocalCreate, MaterialLocalUpdate


def listar(db: Session, apenas_ativos: bool = True) -> list[MaterialLocal]:
    consulta = select(MaterialLocal).order_by(MaterialLocal.nome)
    if apenas_ativos:
        consulta = consulta.where(MaterialLocal.ativo.is_(True))
    return list(db.scalars(consulta).all())


def buscar(db: Session, local_id: int) -> MaterialLocal | None:
    return db.get(MaterialLocal, local_id)


def criar(db: Session, dados: MaterialLocalCreate) -> MaterialLocal:
    local = MaterialLocal(**dados.model_dump())
    db.add(local)
    db.commit()
    db.refresh(local)
    return local


def atualizar(db: Session, local: MaterialLocal, dados: MaterialLocalUpdate) -> MaterialLocal:
    for campo, valor in dados.model_dump().items():
        setattr(local, campo, valor)
    db.commit()
    db.refresh(local)
    return local


def inativar(db: Session, local: MaterialLocal) -> None:
    local.ativo = False
    db.commit()
