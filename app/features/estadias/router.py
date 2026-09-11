from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.estadias import service
from app.features.estadias.models import SituacaoEstadia
from app.features.estadias.schemas import (
    EstadiaAcompanhanteCreate,
    EstadiaAcompanhanteResponse,
    EstadiaCreate,
    EstadiaResponse,
    EstadiaResumoResponse,
    EstadiaUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    id_pessoa: int | None = None,
    situacao: SituacaoEstadia | None = None,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    itens, total = service.listar(db, id_pessoa=id_pessoa, situacao=situacao, skip=skip, take=take)
    return {"items": [EstadiaResumoResponse.model_validate(e) for e in itens], "total": total}


@router.get("/{estadia_id}", response_model=EstadiaResponse)
def buscar(estadia_id: int, db: Session = Depends(get_db)) -> EstadiaResponse:
    estadia = service.buscar(db, estadia_id)
    if estadia is None:
        raise HTTPException(status_code=404, detail="Estadia não encontrada")
    return EstadiaResponse.model_validate(estadia)


@router.post("", response_model=EstadiaResponse, status_code=201)
def criar(dados: EstadiaCreate, db: Session = Depends(get_db)) -> EstadiaResponse:
    return EstadiaResponse.model_validate(service.criar(db, dados))


@router.put("/{estadia_id}", response_model=EstadiaResponse)
def atualizar(estadia_id: int, dados: EstadiaUpdate, db: Session = Depends(get_db)) -> EstadiaResponse:
    estadia = service.buscar(db, estadia_id)
    if estadia is None:
        raise HTTPException(status_code=404, detail="Estadia não encontrada")
    return EstadiaResponse.model_validate(service.atualizar(db, estadia, dados))


@router.post("/{estadia_id}/encerrar", response_model=EstadiaResponse)
def encerrar(estadia_id: int, db: Session = Depends(get_db)) -> EstadiaResponse:
    estadia = service.buscar(db, estadia_id)
    if estadia is None:
        raise HTTPException(status_code=404, detail="Estadia não encontrada")
    return EstadiaResponse.model_validate(service.encerrar(db, estadia))


@router.get("/{estadia_id}/acompanhantes", response_model=list[EstadiaAcompanhanteResponse])
def listar_acompanhantes(estadia_id: int, db: Session = Depends(get_db)) -> list[EstadiaAcompanhanteResponse]:
    estadia = service.buscar(db, estadia_id)
    if estadia is None:
        raise HTTPException(status_code=404, detail="Estadia não encontrada")
    return [
        EstadiaAcompanhanteResponse.model_validate(a)
        for a in service.listar_acompanhantes(db, estadia_id)
    ]


@router.post(
    "/{estadia_id}/acompanhantes", response_model=EstadiaAcompanhanteResponse, status_code=201
)
def adicionar_acompanhante(
    estadia_id: int, dados: EstadiaAcompanhanteCreate, db: Session = Depends(get_db)
) -> EstadiaAcompanhanteResponse:
    estadia = service.buscar(db, estadia_id)
    if estadia is None:
        raise HTTPException(status_code=404, detail="Estadia não encontrada")
    return EstadiaAcompanhanteResponse.model_validate(
        service.adicionar_acompanhante(db, estadia_id, dados)
    )
