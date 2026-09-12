from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.emprestimos import service
from app.features.emprestimos.schemas import (
    EmprestimoCreate,
    EmprestimoDevolverRequest,
    EmprestimoHistoricoResponse,
    EmprestimoItemCreate,
    EmprestimoItemResponse,
    EmprestimoItemUpdate,
    EmprestimoResponse,
    EmprestimoResumoResponse,
    EmprestimoUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    id_pessoa: int | None = None,
    situacao: str | None = None,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    itens, total = service.listar(db, id_pessoa=id_pessoa, situacao=situacao, skip=skip, take=take)
    return {"items": [EmprestimoResumoResponse.model_validate(e) for e in itens], "total": total}


@router.get("/{emprestimo_id}", response_model=EmprestimoResponse)
def buscar(emprestimo_id: int, db: Session = Depends(get_db)) -> EmprestimoResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return EmprestimoResponse.model_validate(emprestimo)


@router.post("", response_model=EmprestimoResponse, status_code=201)
def criar(dados: EmprestimoCreate, db: Session = Depends(get_db)) -> EmprestimoResponse:
    return EmprestimoResponse.model_validate(service.criar(db, dados))


@router.put("/{emprestimo_id}", response_model=EmprestimoResponse)
def atualizar(
    emprestimo_id: int, dados: EmprestimoUpdate, db: Session = Depends(get_db)
) -> EmprestimoResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return EmprestimoResponse.model_validate(service.atualizar(db, emprestimo, dados))


@router.delete("/{emprestimo_id}", status_code=204)
def inativar(emprestimo_id: int, db: Session = Depends(get_db)) -> None:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    service.inativar(db, emprestimo)


@router.post("/{emprestimo_id}/devolver", response_model=EmprestimoResponse)
def devolver(
    emprestimo_id: int, dados: EmprestimoDevolverRequest, db: Session = Depends(get_db)
) -> EmprestimoResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return EmprestimoResponse.model_validate(
        service.devolver(db, emprestimo, dados.id_usuario, dados.data_devolucao)
    )


@router.get("/{emprestimo_id}/itens", response_model=list[EmprestimoItemResponse])
def listar_itens(emprestimo_id: int, db: Session = Depends(get_db)) -> list[EmprestimoItemResponse]:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return [EmprestimoItemResponse.model_validate(i) for i in service.listar_itens(db, emprestimo_id)]


@router.post("/{emprestimo_id}/itens", response_model=EmprestimoItemResponse, status_code=201)
def adicionar_item(
    emprestimo_id: int, dados: EmprestimoItemCreate, db: Session = Depends(get_db)
) -> EmprestimoItemResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return EmprestimoItemResponse.model_validate(service.adicionar_item(db, emprestimo_id, dados))


@router.put("/{emprestimo_id}/itens/{item_id}", response_model=EmprestimoItemResponse)
def atualizar_item(
    emprestimo_id: int,
    item_id: int,
    dados: EmprestimoItemUpdate,
    db: Session = Depends(get_db),
) -> EmprestimoItemResponse:
    item = service.buscar_item(db, item_id)
    if item is None or item.id_emprestimo != emprestimo_id:
        raise HTTPException(status_code=404, detail="Item de empréstimo não encontrado")
    return EmprestimoItemResponse.model_validate(service.atualizar_item(db, item, dados))


@router.get("/{emprestimo_id}/historico", response_model=list[EmprestimoHistoricoResponse])
def listar_historico(emprestimo_id: int, db: Session = Depends(get_db)) -> list[EmprestimoHistoricoResponse]:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return [
        EmprestimoHistoricoResponse.model_validate(h) for h in service.listar_historico(db, emprestimo_id)
    ]
