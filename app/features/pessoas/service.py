from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.features.composicao_familiar.models import ComposicaoFamiliar
from app.features.pessoas.models import Pessoa, PessoaContato
from app.features.pessoas.schemas import (
    PessoaContatoCreate,
    PessoaContatoUpdate,
    PessoaCreate,
    PessoaUpdate,
)


def listar(db: Session, busca: str | None = None, skip: int = 0, take: int = 50) -> tuple[list[Pessoa], int]:
    consulta = select(Pessoa).where(Pessoa.ativo.is_(True)).options(selectinload(Pessoa.contatos))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(or_(Pessoa.nome.ilike(termo), Pessoa.cpf.ilike(termo)))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Pessoa.nome).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, pessoa_id: int) -> Pessoa | None:
    return db.get(Pessoa, pessoa_id)


def criar(db: Session, dados: PessoaCreate) -> Pessoa:
    campos_pessoa = dados.model_dump(exclude={"composicao_familiar", "contatos"})
    pessoa = Pessoa(**campos_pessoa, data_cadastro=date.today())
    db.add(pessoa)
    db.flush()  # gera pessoa.id sem fechar a transação, pra usar como FK abaixo

    for membro in dados.composicao_familiar:
        db.add(ComposicaoFamiliar(id_pessoa=pessoa.id, **membro.model_dump()))

    for contato in dados.contatos:
        db.add(PessoaContato(id_pessoa=pessoa.id, **contato.model_dump()))

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


def listar_contatos(db: Session, pessoa_id: int) -> list[PessoaContato]:
    consulta = select(PessoaContato).where(PessoaContato.id_pessoa == pessoa_id)
    return list(db.scalars(consulta.order_by(PessoaContato.id)).all())


def buscar_contato(db: Session, contato_id: int) -> PessoaContato | None:
    return db.get(PessoaContato, contato_id)


def criar_contato(db: Session, pessoa_id: int, dados: PessoaContatoCreate) -> PessoaContato:
    contato = PessoaContato(id_pessoa=pessoa_id, **dados.model_dump())
    db.add(contato)
    db.commit()
    db.refresh(contato)
    return contato


def atualizar_contato(db: Session, contato: PessoaContato, dados: PessoaContatoUpdate) -> PessoaContato:
    for campo, valor in dados.model_dump().items():
        setattr(contato, campo, valor)
    db.commit()
    db.refresh(contato)
    return contato


def remover_contato(db: Session, contato: PessoaContato) -> None:
    db.delete(contato)
    db.commit()
