from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.materiais import service
from app.features.materiais.schemas import (
    MaterialCreate,
    MaterialResponse,
    MaterialResumoResponse,
    MaterialUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    busca: str | None = None,
    apenas_disponiveis_emprestimo: bool = False,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    itens, total = service.listar(
        db,
        busca=busca,
        apenas_disponiveis_emprestimo=apenas_disponiveis_emprestimo,
        skip=skip,
        take=take,
    )
    return {"items": [MaterialResumoResponse.model_validate(m) for m in itens], "total": total}


@router.get("/{material_id}", response_model=MaterialResponse)
def buscar(material_id: int, db: Session = Depends(get_db)) -> MaterialResponse:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    return MaterialResponse.model_validate(material)


@router.post("", response_model=MaterialResponse, status_code=201)
def criar(dados: MaterialCreate, db: Session = Depends(get_db)) -> MaterialResponse:
    return MaterialResponse.model_validate(service.criar(db, dados))


@router.put("/{material_id}", response_model=MaterialResponse)
def atualizar(material_id: int, dados: MaterialUpdate, db: Session = Depends(get_db)) -> MaterialResponse:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    return MaterialResponse.model_validate(service.atualizar(db, material, dados))


@router.delete("/{material_id}", status_code=204)
def inativar(material_id: int, db: Session = Depends(get_db)) -> None:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    service.inativar(db, material)
