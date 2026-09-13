from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.hospitais import service
from app.features.hospitais.schemas import HospitalCreate, HospitalResponse, HospitalUpdate

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


@router.post("", response_model=HospitalResponse, status_code=201)
def criar(dados: HospitalCreate, db: Session = Depends(get_db)) -> HospitalResponse:
    return HospitalResponse.model_validate(service.criar(db, dados))


@router.put("/{hospital_id}", response_model=HospitalResponse)
def atualizar(hospital_id: int, dados: HospitalUpdate, db: Session = Depends(get_db)) -> HospitalResponse:
    hospital = service.buscar(db, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    return HospitalResponse.model_validate(service.atualizar(db, hospital, dados))


@router.delete("/{hospital_id}", status_code=204)
def inativar(hospital_id: int, db: Session = Depends(get_db)) -> None:
    hospital = service.buscar(db, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital não encontrado")
    service.inativar(db, hospital)
