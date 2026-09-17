from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import usuario_atual
from app.features.relatorios import service
from app.features.relatorios.schemas import (
    FiltroSituacaoEmprestimo,
    FiltroSituacaoEstadia,
    PeriodoRelatorio,
    RelatorioResumoResponse,
)

router = APIRouter(dependencies=[Depends(usuario_atual)])


@router.get("/pessoas/resumo", response_model=RelatorioResumoResponse)
def resumo_pessoas(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL, db: Session = Depends(get_db)
) -> RelatorioResumoResponse:
    return RelatorioResumoResponse(itens=service.resumo_pessoas(db, periodo))


@router.get("/pessoas/pdf")
def relatorio_pessoas(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL, db: Session = Depends(get_db)
) -> Response:
    return Response(content=service.gerar_pdf_pessoas(db, periodo), media_type="application/pdf")


@router.get("/estadias/resumo", response_model=RelatorioResumoResponse)
def resumo_estadias(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL,
    situacao: FiltroSituacaoEstadia = FiltroSituacaoEstadia.TODOS,
    db: Session = Depends(get_db),
) -> RelatorioResumoResponse:
    return RelatorioResumoResponse(itens=service.resumo_estadias(db, periodo, situacao))


@router.get("/estadias/pdf")
def relatorio_estadias(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL,
    situacao: FiltroSituacaoEstadia = FiltroSituacaoEstadia.TODOS,
    db: Session = Depends(get_db),
) -> Response:
    return Response(content=service.gerar_pdf_estadias(db, periodo, situacao), media_type="application/pdf")


@router.get("/materiais/resumo", response_model=RelatorioResumoResponse)
def resumo_materiais(db: Session = Depends(get_db)) -> RelatorioResumoResponse:
    return RelatorioResumoResponse(itens=service.resumo_materiais(db))


@router.get("/materiais/pdf")
def relatorio_materiais(db: Session = Depends(get_db)) -> Response:
    return Response(content=service.gerar_pdf_materiais(db), media_type="application/pdf")


@router.get("/emprestimos/resumo", response_model=RelatorioResumoResponse)
def resumo_emprestimos(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL,
    situacao: FiltroSituacaoEmprestimo = FiltroSituacaoEmprestimo.TODOS,
    db: Session = Depends(get_db),
) -> RelatorioResumoResponse:
    return RelatorioResumoResponse(itens=service.resumo_emprestimos(db, periodo, situacao))


@router.get("/emprestimos/pdf")
def relatorio_emprestimos(
    periodo: PeriodoRelatorio = PeriodoRelatorio.MENSAL,
    situacao: FiltroSituacaoEmprestimo = FiltroSituacaoEmprestimo.TODOS,
    db: Session = Depends(get_db),
) -> Response:
    return Response(
        content=service.gerar_pdf_emprestimos(db, periodo, situacao), media_type="application/pdf"
    )
