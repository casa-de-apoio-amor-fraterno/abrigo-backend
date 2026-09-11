from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.pessoas.models import Pessoa
from app.features.pessoas.schemas import PessoaCreate, PessoaUpdate


def listar(db: Session, busca: str | None = None, skip: int = 0, take: int = 50) -> tuple[list[Pessoa], int]:
    consulta = select(Pessoa).where(Pessoa.ativo.is_(True))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(or_(Pessoa.nome.ilike(termo), Pessoa.cpf.ilike(termo)))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Pessoa.nome).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, pessoa_id: int) -> Pessoa | None:
    return db.get(Pessoa, pessoa_id)


def criar(db: Session, dados: PessoaCreate) -> Pessoa:
    pessoa = Pessoa(**dados.model_dump(), data_cadastro=date.today())
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


TIPOS_FOTO_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
TAMANHO_MAXIMO_FOTO_BYTES = 5 * 1024 * 1024


class FotoInvalida(Exception):
    pass


def salvar_foto(db: Session, pessoa: Pessoa, conteudo: bytes, content_type: str | None) -> Pessoa:
    if content_type not in TIPOS_FOTO_PERMITIDOS:
        raise FotoInvalida("Formato de imagem não suportado — envie JPEG, PNG ou WebP.")
    if len(conteudo) > TAMANHO_MAXIMO_FOTO_BYTES:
        raise FotoInvalida("Imagem maior que o limite permitido (5MB).")

    pessoa.foto = conteudo
    pessoa.foto_content_type = content_type
    db.commit()
    db.refresh(pessoa)
    return pessoa


def remover_foto(db: Session, pessoa: Pessoa) -> None:
    pessoa.foto = None
    pessoa.foto_content_type = None
    db.commit()
