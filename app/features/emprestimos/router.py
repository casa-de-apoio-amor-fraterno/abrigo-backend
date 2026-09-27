from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import usuario_atual
from app.features.emprestimos import service
from app.features.emprestimos.schemas import (
    AlertaVencimentoEmprestimo,
    EmprestimoContratoCreate,
    EmprestimoContratoResponse,
    EmprestimoCreate,
    EmprestimoDevolverRequest,
    EmprestimoHistoricoResponse,
    EmprestimoItemCreate,
    EmprestimoItemResponse,
    EmprestimoItemUpdate,
    EmprestimoResponse,
    EmprestimoResumoResponse,
    EmprestimoUpdate,
    SituacaoEmprestimo,
)
from app.features.usuarios.models import Usuario
from app.shared.imagem import Base64Invalido

router = APIRouter(dependencies=[Depends(usuario_atual)])


@router.get("")
def listar(
    id_pessoa: int | None = None,
    situacao: SituacaoEmprestimo | None = None,
    busca: str | None = None,
    data_devolucao_inicio: date | None = None,
    data_devolucao_fim: date | None = None,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    itens, total = service.listar(
        db,
        id_pessoa=id_pessoa,
        situacao=situacao,
        busca=busca,
        data_devolucao_inicio=data_devolucao_inicio,
        data_devolucao_fim=data_devolucao_fim,
        skip=skip,
        take=take,
    )
    return {"items": [EmprestimoResumoResponse.model_validate(e) for e in itens], "total": total}


@router.get("/alertas-vencimento", response_model=list[AlertaVencimentoEmprestimo])
def listar_alertas_vencimento(
    dias: int = service.DIAS_HORIZONTE_ALERTA_VENCIMENTO, db: Session = Depends(get_db)
) -> list[AlertaVencimentoEmprestimo]:
    return [
        AlertaVencimentoEmprestimo.model_validate(alerta)
        for alerta in service.listar_alertas_vencimento(db, dias_horizonte=dias)
    ]


@router.get("/{emprestimo_id}", response_model=EmprestimoResponse)
def buscar(emprestimo_id: int, db: Session = Depends(get_db)) -> EmprestimoResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return EmprestimoResponse.model_validate(emprestimo)


@router.post("", response_model=EmprestimoResponse, status_code=201)
def criar(dados: EmprestimoCreate, db: Session = Depends(get_db)) -> EmprestimoResponse:
    try:
        return EmprestimoResponse.model_validate(service.criar(db, dados))
    except service.MaterialJaNoEmprestimo as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    try:
        return EmprestimoItemResponse.model_validate(service.adicionar_item(db, emprestimo_id, dados))
    except service.MaterialJaNoEmprestimo as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    try:
        return EmprestimoItemResponse.model_validate(service.atualizar_item(db, item, dados))
    except service.MaterialJaNoEmprestimo as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{emprestimo_id}/historico", response_model=list[EmprestimoHistoricoResponse])
def listar_historico(emprestimo_id: int, db: Session = Depends(get_db)) -> list[EmprestimoHistoricoResponse]:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return [
        EmprestimoHistoricoResponse.model_validate(h) for h in service.listar_historico(db, emprestimo_id)
    ]


@router.get("/{emprestimo_id}/contratos", response_model=list[EmprestimoContratoResponse])
def listar_contratos(emprestimo_id: int, db: Session = Depends(get_db)) -> list[EmprestimoContratoResponse]:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return [EmprestimoContratoResponse.model_validate(c) for c in service.listar_contratos(db, emprestimo_id)]


@router.get("/{emprestimo_id}/contratos/{contrato_id}/pdf")
def obter_pdf_contrato(emprestimo_id: int, contrato_id: int, db: Session = Depends(get_db)) -> Response:
    contrato = service.buscar_contrato(db, contrato_id)
    if contrato is None or contrato.id_emprestimo != emprestimo_id:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return Response(content=contrato.pdf, media_type="application/pdf")


@router.post(
    "/{emprestimo_id}/contrato",
    response_model=EmprestimoContratoResponse,
    status_code=201,
)
def assinar_contrato(
    emprestimo_id: int,
    dados: EmprestimoContratoCreate,
    usuario: Usuario = Depends(usuario_atual),
    db: Session = Depends(get_db),
) -> EmprestimoContratoResponse:
    emprestimo = service.buscar(db, emprestimo_id)
    if emprestimo is None:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    try:
        contrato = service.criar_contrato(db, emprestimo, usuario.id, dados.assinatura_png_base64, dados.tipo)
    except service.ContratoJaAssinado as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.RenovacaoSemContratoOriginal as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.ContratoDadosIncompletos as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Base64Invalido as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EmprestimoContratoResponse.model_validate(contrato)
