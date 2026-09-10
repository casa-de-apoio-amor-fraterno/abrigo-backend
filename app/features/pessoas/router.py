from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.pessoas import service
from app.features.pessoas.schemas import (
    PessoaCreate,
    PessoaResponse,
    PessoaResumoResponse,
    PessoaUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    busca: str | None = None, skip: int = 0, take: int = 50, db: Session = Depends(get_db)
) -> dict:
    itens, total = service.listar(db, busca=busca, skip=skip, take=take)
    return {"items": [PessoaResumoResponse.model_validate(p) for p in itens], "total": total}


@router.get("/{pessoa_id}", response_model=PessoaResponse)
def buscar(pessoa_id: int, db: Session = Depends(get_db)) -> PessoaResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaResponse.model_validate(pessoa)


@router.post("", response_model=PessoaResponse, status_code=201)
def criar(dados: PessoaCreate, db: Session = Depends(get_db)) -> PessoaResponse:
    return PessoaResponse.model_validate(service.criar(db, dados))


@router.put("/{pessoa_id}", response_model=PessoaResponse)
def atualizar(pessoa_id: int, dados: PessoaUpdate, db: Session = Depends(get_db)) -> PessoaResponse:
    pessoa = service.buscar(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaResponse.model_validate(service.atualizar(db, pessoa, dados))
