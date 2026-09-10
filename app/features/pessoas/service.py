from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.pessoas.models import Pessoa
from app.features.pessoas.schemas import PessoaCreate, PessoaUpdate


def listar(db: Session, skip: int = 0, take: int = 50) -> tuple[list[Pessoa], int]:
    filtro = Pessoa.ativo.is_(True)
    total = db.scalar(select(func.count()).select_from(Pessoa).where(filtro)) or 0
    itens = db.scalars(select(Pessoa).where(filtro).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, pessoa_id: int) -> Pessoa | None:
    return db.get(Pessoa, pessoa_id)


def criar(db: Session, dados: PessoaCreate) -> Pessoa:
    pessoa = Pessoa(**dados.model_dump())
    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return pessoa


def atualizar(db: Session, pessoa: Pessoa, dados: PessoaUpdate) -> Pessoa:
    for campo, valor in dados.model_dump().items():
        setattr(pessoa, campo, valor)
    db.commit()
    db.refresh(pessoa)
    return pessoa


def inativar(db: Session, pessoa: Pessoa) -> None:
    pessoa.ativo = False
    db.commit()
