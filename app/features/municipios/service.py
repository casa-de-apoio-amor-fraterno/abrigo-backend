from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.municipios.models import Municipio


def listar(db: Session, id_estado: int | None = None, busca: str | None = None) -> list[Municipio]:
    consulta = select(Municipio).order_by(Municipio.nome)
    if id_estado is not None:
        consulta = consulta.where(Municipio.id_estado == id_estado)
    if busca:
        consulta = consulta.where(Municipio.nome.ilike(f"%{busca}%"))
    return list(db.scalars(consulta).all())


def buscar(db: Session, municipio_id: int) -> Municipio | None:
    return db.get(Municipio, municipio_id)
