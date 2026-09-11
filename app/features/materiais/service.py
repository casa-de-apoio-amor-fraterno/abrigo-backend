from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.materiais.models import Material
from app.features.materiais.schemas import MaterialCreate, MaterialUpdate


def listar(
    db: Session,
    busca: str | None = None,
    apenas_disponiveis_emprestimo: bool = False,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[Material], int]:
    consulta = select(Material).where(Material.ativo.is_not(False))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(
            or_(Material.descricao.ilike(termo), Material.codigo_identificacao.ilike(termo))
        )
    if apenas_disponiveis_emprestimo:
        consulta = consulta.where(Material.disponivel_emprestimo.is_(True))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Material.descricao).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, material_id: int) -> Material | None:
    return db.get(Material, material_id)


def criar(db: Session, dados: MaterialCreate) -> Material:
    material = Material(**dados.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def atualizar(db: Session, material: Material, dados: MaterialUpdate) -> Material:
    for campo, valor in dados.model_dump().items():
        setattr(material, campo, valor)
    db.commit()
    db.refresh(material)
    return material


def inativar(db: Session, material: Material) -> None:
    material.ativo = False
    db.commit()
