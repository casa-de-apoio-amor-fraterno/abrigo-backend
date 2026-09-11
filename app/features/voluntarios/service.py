from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.voluntarios.models import Voluntario
from app.features.voluntarios.schemas import VoluntarioCreate, VoluntarioUpdate


def listar(
    db: Session, busca: str | None = None, skip: int = 0, take: int = 50
) -> tuple[list[Voluntario], int]:
    consulta = select(Voluntario).where(Voluntario.ativo.is_(True))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(or_(Voluntario.nome.ilike(termo), Voluntario.cpf.ilike(termo)))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Voluntario.nome).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, voluntario_id: int) -> Voluntario | None:
    return db.get(Voluntario, voluntario_id)


def criar(db: Session, dados: VoluntarioCreate) -> Voluntario:
    voluntario = Voluntario(**dados.model_dump())
    db.add(voluntario)
    db.commit()
    db.refresh(voluntario)
    return voluntario


def atualizar(db: Session, voluntario: Voluntario, dados: VoluntarioUpdate) -> Voluntario:
    for campo, valor in dados.model_dump().items():
        setattr(voluntario, campo, valor)
    db.commit()
    db.refresh(voluntario)
    return voluntario


def inativar(db: Session, voluntario: Voluntario) -> None:
    voluntario.ativo = False
    db.commit()
