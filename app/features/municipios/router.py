from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.municipios import service
from app.features.municipios.schemas import MunicipioResponse

router = APIRouter()


@router.get("", response_model=list[MunicipioResponse])
def listar(
    id_estado: int | None = None, busca: str | None = None, db: Session = Depends(get_db)
) -> list[MunicipioResponse]:
    return [
        MunicipioResponse.model_validate(m)
        for m in service.listar(db, id_estado=id_estado, busca=busca)
    ]


@router.get("/{municipio_id}", response_model=MunicipioResponse)
def buscar(municipio_id: int, db: Session = Depends(get_db)) -> MunicipioResponse:
    municipio = service.buscar(db, municipio_id)
    if municipio is None:
        raise HTTPException(status_code=404, detail="Município não encontrado")
    return MunicipioResponse.model_validate(municipio)
