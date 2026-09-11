from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import exigir_perfil
from app.features.composicao_familiar import service
from app.features.composicao_familiar.schemas import (
    ComposicaoFamiliarCreate,
    ComposicaoFamiliarResponse,
    ComposicaoFamiliarUpdate,
)

router = APIRouter(dependencies=[Depends(exigir_perfil("Assistente Social"))])


@router.get("", response_model=list[ComposicaoFamiliarResponse])
def listar(pessoa_id: int, db: Session = Depends(get_db)) -> list[ComposicaoFamiliarResponse]:
    return [
        ComposicaoFamiliarResponse.model_validate(m)
        for m in service.listar_por_pessoa(db, pessoa_id)
    ]


@router.post("", response_model=ComposicaoFamiliarResponse, status_code=201)
def criar(
    pessoa_id: int, dados: ComposicaoFamiliarCreate, db: Session = Depends(get_db)
) -> ComposicaoFamiliarResponse:
    return ComposicaoFamiliarResponse.model_validate(service.criar(db, pessoa_id, dados))


@router.put("/{membro_id}", response_model=ComposicaoFamiliarResponse)
def atualizar(
    pessoa_id: int,
    membro_id: int,
    dados: ComposicaoFamiliarUpdate,
    db: Session = Depends(get_db),
) -> ComposicaoFamiliarResponse:
    membro = service.buscar(db, membro_id)
    if membro is None or membro.id_pessoa != pessoa_id:
        raise HTTPException(status_code=404, detail="Membro da composição familiar não encontrado")
    return ComposicaoFamiliarResponse.model_validate(service.atualizar(db, membro, dados))


@router.delete("/{membro_id}", status_code=204)
def remover(pessoa_id: int, membro_id: int, db: Session = Depends(get_db)) -> None:
    membro = service.buscar(db, membro_id)
    if membro is None or membro.id_pessoa != pessoa_id:
        raise HTTPException(status_code=404, detail="Membro da composição familiar não encontrado")
    service.remover(db, membro)
