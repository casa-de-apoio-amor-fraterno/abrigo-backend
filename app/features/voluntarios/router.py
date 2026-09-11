from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.voluntarios import service
from app.features.voluntarios.schemas import (
    VoluntarioCreate,
    VoluntarioResponse,
    VoluntarioResumoResponse,
    VoluntarioUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    busca: str | None = None, skip: int = 0, take: int = 50, db: Session = Depends(get_db)
) -> dict:
    itens, total = service.listar(db, busca=busca, skip=skip, take=take)
    return {"items": [VoluntarioResumoResponse.model_validate(v) for v in itens], "total": total}


@router.get("/{voluntario_id}", response_model=VoluntarioResponse)
def buscar(voluntario_id: int, db: Session = Depends(get_db)) -> VoluntarioResponse:
    voluntario = service.buscar(db, voluntario_id)
    if voluntario is None:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")
    return VoluntarioResponse.model_validate(voluntario)


@router.post("", response_model=VoluntarioResponse, status_code=201)
def criar(dados: VoluntarioCreate, db: Session = Depends(get_db)) -> VoluntarioResponse:
    return VoluntarioResponse.model_validate(service.criar(db, dados))


@router.put("/{voluntario_id}", response_model=VoluntarioResponse)
def atualizar(
    voluntario_id: int, dados: VoluntarioUpdate, db: Session = Depends(get_db)
) -> VoluntarioResponse:
    voluntario = service.buscar(db, voluntario_id)
    if voluntario is None:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")
    return VoluntarioResponse.model_validate(service.atualizar(db, voluntario, dados))


@router.delete("/{voluntario_id}", status_code=204)
def inativar(voluntario_id: int, db: Session = Depends(get_db)) -> None:
    voluntario = service.buscar(db, voluntario_id)
    if voluntario is None:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado")
    service.inativar(db, voluntario)
