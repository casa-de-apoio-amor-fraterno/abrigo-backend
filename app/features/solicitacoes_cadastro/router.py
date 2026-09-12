from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import usuario_atual
from app.features.pessoas.service import FotoInvalida
from app.features.solicitacoes_cadastro import service
from app.features.solicitacoes_cadastro.models import SituacaoSolicitacaoCadastro
from app.features.solicitacoes_cadastro.schemas import (
    SolicitacaoCadastroResponse,
    SolicitacaoCadastroResumoResponse,
)
from app.features.usuarios.models import Usuario

router = APIRouter()


@router.get("", dependencies=[Depends(usuario_atual)])
def listar(
    situacao: SituacaoSolicitacaoCadastro | None = None,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    # Listar/aprovar/revogar exige login (`usuario_atual`) — só a criação
    # (abaixo) é pública, pra ser possível pelo próprio celular do paciente
    # sem sessão nenhuma.
    itens, total = service.listar(db, situacao=situacao, skip=skip, take=take)
    return {
        "items": [SolicitacaoCadastroResumoResponse.model_validate(s) for s in itens],
        "total": total,
    }


@router.post("", response_model=SolicitacaoCadastroResponse, status_code=201)
def criar(
    nome: str = Form(...),
    data_nascimento: date = Form(...),
    cpf: str | None = Form(None),
    telefone: str | None = Form(None),
    arquivo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> SolicitacaoCadastroResponse:
    # Público, sem login — mesmo padrão de `POST /pessoas` (ver
    # app/features/pessoas/router.py): é assim que o paciente se
    # auto-cadastra pelo próprio celular, antes de existir qualquer sessão.
    conteudo = arquivo.file.read() if arquivo is not None else None
    content_type = arquivo.content_type if arquivo is not None else None
    try:
        solicitacao = service.criar(db, nome, data_nascimento, cpf, telefone, conteudo, content_type)
    except FotoInvalida as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SolicitacaoCadastroResponse.model_validate(solicitacao)


@router.get("/{solicitacao_id}/foto", dependencies=[Depends(usuario_atual)])
def obter_foto(solicitacao_id: int, db: Session = Depends(get_db)) -> Response:
    solicitacao = service.buscar(db, solicitacao_id)
    if solicitacao is None or solicitacao.foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    return Response(
        content=solicitacao.foto, media_type=solicitacao.foto_content_type or "image/jpeg"
    )


@router.post("/{solicitacao_id}/aprovar", response_model=SolicitacaoCadastroResponse)
def aprovar(
    solicitacao_id: int,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> SolicitacaoCadastroResponse:
    solicitacao = service.buscar(db, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    try:
        solicitacao = service.aprovar(db, solicitacao, usuario.id)
    except service.SolicitacaoJaAnalisada as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SolicitacaoCadastroResponse.model_validate(solicitacao)


@router.post("/{solicitacao_id}/revogar", response_model=SolicitacaoCadastroResponse)
def revogar(
    solicitacao_id: int,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> SolicitacaoCadastroResponse:
    solicitacao = service.buscar(db, solicitacao_id)
    if solicitacao is None:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    try:
        solicitacao = service.revogar(db, solicitacao, usuario.id)
    except service.SolicitacaoJaAnalisada as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SolicitacaoCadastroResponse.model_validate(solicitacao)
