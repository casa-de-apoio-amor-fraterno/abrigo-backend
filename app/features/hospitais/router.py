from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.hospitais import service
from app.features.hospitais.schemas import HospitalResponse

router = APIRouter()


@router.get("", response_model=list[HospitalResponse])
def listar(apenas_ativos: bool = True, db: Session = Depends(get_db)) -> list[HospitalResponse]:
    return [HospitalResponse.model_validate(h) for h in service.listar(db, apenas_ativos=apenas_ativos)]


@router.get("/{hospital_id}", response_model=HospitalResponse)
def buscar(hospital_id: int, db: Session = Depends(get_db)) -> HospitalResponse:
    hospital = service.buscar(db, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    return HospitalResponse.model_validate(hospital)
