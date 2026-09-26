from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import usuario_atual
from app.features.materiais_locais import service
from app.features.materiais_locais.schemas import (
    MaterialLocalCreate,
    MaterialLocalResponse,
    MaterialLocalUpdate,
)

router = APIRouter(dependencies=[Depends(usuario_atual)])


@router.get("", response_model=list[MaterialLocalResponse])
def listar(apenas_ativos: bool = True, db: Session = Depends(get_db)) -> list[MaterialLocalResponse]:
    return [MaterialLocalResponse.model_validate(l) for l in service.listar(db, apenas_ativos=apenas_ativos)]


@router.get("/{local_id}", response_model=MaterialLocalResponse)
def buscar(local_id: int, db: Session = Depends(get_db)) -> MaterialLocalResponse:
    local = service.buscar(db, local_id)
    if local is None:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    return MaterialLocalResponse.model_validate(local)


@router.post("", response_model=MaterialLocalResponse, status_code=201)
def criar(dados: MaterialLocalCreate, db: Session = Depends(get_db)) -> MaterialLocalResponse:
    return MaterialLocalResponse.model_validate(service.criar(db, dados))


@router.put("/{local_id}", response_model=MaterialLocalResponse)
def atualizar(local_id: int, dados: MaterialLocalUpdate, db: Session = Depends(get_db)) -> MaterialLocalResponse:
    local = service.buscar(db, local_id)
    if local is None:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    return MaterialLocalResponse.model_validate(service.atualizar(db, local, dados))


@router.delete("/{local_id}", status_code=204)
def inativar(local_id: int, db: Session = Depends(get_db)) -> None:
    local = service.buscar(db, local_id)
    if local is None:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    service.inativar(db, local)
