from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.quartos import service
from app.features.quartos.schemas import (
    QuartoCreate,
    QuartoOcupacaoResponse,
    QuartoResponse,
    QuartoUpdate,
)

router = APIRouter()


@router.get("", response_model=list[QuartoResponse])
def listar(apenas_ativos: bool = True, db: Session = Depends(get_db)) -> list[QuartoResponse]:
    return [QuartoResponse.model_validate(q) for q in service.listar(db, apenas_ativos=apenas_ativos)]


# Precisa vir antes de `/{quarto_id}` — senão "ocupacao" seria interpretado
# como o parâmetro `quarto_id: int` e daria 422 em vez de bater aqui.
@router.get("/ocupacao", response_model=list[QuartoOcupacaoResponse])
def listar_ocupacao(db: Session = Depends(get_db)) -> list[QuartoOcupacaoResponse]:
    return [QuartoOcupacaoResponse.model_validate(q) for q in service.listar_ocupacao(db)]


@router.get("/{quarto_id}", response_model=QuartoResponse)
def buscar(quarto_id: int, db: Session = Depends(get_db)) -> QuartoResponse:
    quarto = service.buscar(db, quarto_id)
    if quarto is None:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    return QuartoResponse.model_validate(quarto)


@router.post("", response_model=QuartoResponse, status_code=201)
def criar(dados: QuartoCreate, db: Session = Depends(get_db)) -> QuartoResponse:
    return QuartoResponse.model_validate(service.criar(db, dados))


@router.put("/{quarto_id}", response_model=QuartoResponse)
def atualizar(quarto_id: int, dados: QuartoUpdate, db: Session = Depends(get_db)) -> QuartoResponse:
    quarto = service.buscar(db, quarto_id)
    if quarto is None:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    return QuartoResponse.model_validate(service.atualizar(db, quarto, dados))


@router.delete("/{quarto_id}", status_code=204)
def inativar(quarto_id: int, db: Session = Depends(get_db)) -> None:
    quarto = service.buscar(db, quarto_id)
    if quarto is None:
        raise HTTPException(status_code=404, detail="Quarto não encontrado")
    service.inativar(db, quarto)
