from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import usuario_atual_opcional
from app.features.pessoas import service
from app.features.pessoas.schemas import (
    PessoaContatoCreate,
    PessoaContatoResponse,
    PessoaContatoUpdate,
    PessoaCreate,
    PessoaResponse,
    PessoaResumoResponse,
    PessoaUpdate,
)
from app.features.usuarios.models import Usuario

router = APIRouter()


@router.get("")
def listar(
    busca: str | None = None, skip: int = 0, take: int = 50, db: Session = Depends(get_db)
) -> dict:
    itens, total = service.listar(db, busca=busca, skip=skip, take=take)
    return {"items": [PessoaResumoResponse.model_validate(p) for p in itens], "total": total}


@router.get("/{pessoa_id}", response_model=PessoaResponse)
def buscar(pessoa_id: int, db: Session = Depends(get_db)) -> PessoaResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaResponse.model_validate(pessoa)


@router.post("", response_model=PessoaResponse, status_code=201)
def criar(
    dados: PessoaCreate,
    usuario: Usuario | None = Depends(usuario_atual_opcional),
    db: Session = Depends(get_db),
) -> PessoaResponse:
    # Criar pessoa não exige login (nunca exigiu). Composição familiar é
    # que é dado sensível (ver app/features/composicao_familiar/router.py,
    # `exigir_perfil`) — mesma trava aqui, só quando ela chega aninhada
    # nesse POST, pra não quebrar o caso comum (sem composição familiar)
    # que sempre funcionou sem autenticação.
    if dados.composicao_familiar and (usuario is None or usuario.perfil != "Assistente Social"):
        raise HTTPException(status_code=403, detail="Acesso restrito a este perfil")
    return PessoaResponse.model_validate(service.criar(db, dados))


@router.put("/{pessoa_id}", response_model=PessoaResponse)
def atualizar(pessoa_id: int, dados: PessoaUpdate, db: Session = Depends(get_db)) -> PessoaResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaResponse.model_validate(service.atualizar(db, pessoa, dados))


@router.delete("/{pessoa_id}", status_code=204)
def inativar(pessoa_id: int, db: Session = Depends(get_db)) -> None:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    service.inativar(db, pessoa)


@router.get("/{pessoa_id}/foto")
def obter_foto(pessoa_id: int, db: Session = Depends(get_db)) -> Response:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None or pessoa.foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    return Response(content=pessoa.foto, media_type=pessoa.foto_content_type or "image/jpeg")


@router.put("/{pessoa_id}/foto", response_model=PessoaResponse)
def salvar_foto(
    pessoa_id: int, arquivo: UploadFile = File(...), db: Session = Depends(get_db)
) -> PessoaResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    conteudo = arquivo.file.read()
    try:
        pessoa = service.salvar_foto(db, pessoa, conteudo, arquivo.content_type)
    except service.FotoInvalida as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PessoaResponse.model_validate(pessoa)


@router.delete("/{pessoa_id}/foto", status_code=204)
def remover_foto(pessoa_id: int, db: Session = Depends(get_db)) -> None:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    service.remover_foto(db, pessoa)


@router.get("/{pessoa_id}/contatos", response_model=list[PessoaContatoResponse])
def listar_contatos(pessoa_id: int, db: Session = Depends(get_db)) -> list[PessoaContatoResponse]:
    return [PessoaContatoResponse.model_validate(c) for c in service.listar_contatos(db, pessoa_id)]


@router.post("/{pessoa_id}/contatos", response_model=PessoaContatoResponse, status_code=201)
def criar_contato(
    pessoa_id: int, dados: PessoaContatoCreate, db: Session = Depends(get_db)
) -> PessoaContatoResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaContatoResponse.model_validate(service.criar_contato(db, pessoa_id, dados))


@router.put("/{pessoa_id}/contatos/{contato_id}", response_model=PessoaContatoResponse)
def atualizar_contato(
    pessoa_id: int, contato_id: int, dados: PessoaContatoUpdate, db: Session = Depends(get_db)
) -> PessoaContatoResponse:
    contato = service.buscar_contato(db, contato_id)
    if contato is None or contato.id_pessoa != pessoa_id:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    return PessoaContatoResponse.model_validate(service.atualizar_contato(db, contato, dados))


@router.delete("/{pessoa_id}/contatos/{contato_id}", status_code=204)
def remover_contato(pessoa_id: int, contato_id: int, db: Session = Depends(get_db)) -> None:
    contato = service.buscar_contato(db, contato_id)
    if contato is None or contato.id_pessoa != pessoa_id:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    service.remover_contato(db, contato)
