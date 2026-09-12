from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.pessoas.models import Pessoa, PessoaContato
from app.features.pessoas.service import (
    TAMANHO_MAXIMO_FOTO_BYTES,
    TIPOS_FOTO_PERMITIDOS,
    FotoInvalida,
)
from app.features.solicitacoes_cadastro.models import (
    SituacaoSolicitacaoCadastro,
    SolicitacaoCadastroPaciente,
)


class SolicitacaoJaAnalisada(Exception):
    pass


def listar(
    db: Session,
    situacao: SituacaoSolicitacaoCadastro | None = None,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[SolicitacaoCadastroPaciente], int]:
    consulta = select(SolicitacaoCadastroPaciente)
    if situacao is not None:
        consulta = consulta.where(SolicitacaoCadastroPaciente.situacao == situacao)

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(
        consulta.order_by(SolicitacaoCadastroPaciente.data_solicitacao.desc()).offset(skip).limit(take)
    ).all()
    return list(itens), total


def buscar(db: Session, solicitacao_id: int) -> SolicitacaoCadastroPaciente | None:
    return db.get(SolicitacaoCadastroPaciente, solicitacao_id)


def criar(
    db: Session,
    nome: str,
    data_nascimento: date,
    cpf: str | None,
    telefone: str | None,
    foto_conteudo: bytes | None,
    foto_content_type: str | None,
) -> SolicitacaoCadastroPaciente:
    if foto_conteudo is not None:
        if foto_content_type not in TIPOS_FOTO_PERMITIDOS:
            raise FotoInvalida("Formato de imagem não suportado — envie JPEG, PNG ou WebP.")
        if len(foto_conteudo) > TAMANHO_MAXIMO_FOTO_BYTES:
            raise FotoInvalida("Imagem maior que o limite permitido (5MB).")

    solicitacao = SolicitacaoCadastroPaciente(
        nome=nome,
        data_nascimento=data_nascimento,
        cpf=cpf,
        telefone=telefone,
        foto=foto_conteudo,
        foto_content_type=foto_content_type,
        situacao=SituacaoSolicitacaoCadastro.PENDENTE,
        # Coluna `DateTime` sem timezone (mesmo padrão de
        # `Estadia.data_entrada`/`EmprestimoHistorico.data_cadastro`).
        data_solicitacao=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def aprovar(
    db: Session, solicitacao: SolicitacaoCadastroPaciente, id_usuario: int
) -> SolicitacaoCadastroPaciente:
    if solicitacao.situacao != SituacaoSolicitacaoCadastro.PENDENTE:
        raise SolicitacaoJaAnalisada("Esta solicitação já foi analisada.")

    pessoa = Pessoa(
        nome=solicitacao.nome,
        data_nascimento=solicitacao.data_nascimento,
        cpf=solicitacao.cpf,
        data_cadastro=date.today(),
        foto=solicitacao.foto,
        foto_content_type=solicitacao.foto_content_type,
    )
    if solicitacao.telefone:
        pessoa.contatos = [PessoaContato(numero=solicitacao.telefone, principal=True)]
    db.add(pessoa)
    db.flush()  # gera pessoa.id sem fechar a transação, pra usar como FK abaixo

    solicitacao.situacao = SituacaoSolicitacaoCadastro.APROVADA
    solicitacao.id_pessoa = pessoa.id
    solicitacao.id_usuario_analise = id_usuario
    solicitacao.data_analise = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao


def revogar(
    db: Session, solicitacao: SolicitacaoCadastroPaciente, id_usuario: int
) -> SolicitacaoCadastroPaciente:
    if solicitacao.situacao != SituacaoSolicitacaoCadastro.PENDENTE:
        raise SolicitacaoJaAnalisada("Esta solicitação já foi analisada.")

    solicitacao.situacao = SituacaoSolicitacaoCadastro.REVOGADA
    solicitacao.id_usuario_analise = id_usuario
    solicitacao.data_analise = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(solicitacao)
    return solicitacao
