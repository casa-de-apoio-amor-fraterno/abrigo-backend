from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.estados import service
from app.features.estados.schemas import EstadoResponse

router = APIRouter()


@router.get("", response_model=list[EstadoResponse])
def listar(db: Session = Depends(get_db)) -> list[EstadoResponse]:
    return [EstadoResponse.model_validate(e) for e in service.listar(db)]


@router.get("/{estado_id}", response_model=EstadoResponse)
def buscar(estado_id: int, db: Session = Depends(get_db)) -> EstadoResponse:
    estado = service.buscar(db, estado_id)
    if estado is None:
        raise HTTPException(status_code=404, detail="Estado não encontrado")
    return EstadoResponse.model_validate(estado)
