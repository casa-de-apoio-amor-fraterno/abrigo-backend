"""Endpoints PÚBLICOS (sem login) da assinatura remota do contrato de
comodato — a pessoa abre o link no próprio celular e confirma o CPF. Ver
`link_assinatura.py` e `models.EmprestimoLinkAssinatura` pro desenho de
segurança.

Cada chamada com dados reenvia o CPF (sem sessão/estado no servidor): CPF
errado conta tentativa no link, que trava após o limite. Nada de dado
pessoal sai antes do CPF conferir."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.database import get_db
from app.features.emprestimos import link_assinatura, service
from app.features.emprestimos.schemas import (
    AssinaturaPublicaAssinar,
    AssinaturaPublicaCpf,
    AssinaturaPublicaResumo,
)
from app.shared.imagem import Base64Invalido

router = APIRouter()

_CHAVE_ROTA = "assinatura-publica"


def _chave_ip(request: Request) -> tuple[str, str]:
    return (request.client.host if request.client else "?", _CHAVE_ROTA)


def _freio_ip(request: Request) -> None:
    # Freio contra chute de código/token por IP: só conta quando o link nem
    # existe (ver `LinkNaoEncontrado`), pra não punir quem só errou o CPF
    # (esse já tem o próprio limite por link).
    if rate_limit.limite_excedido(_chave_ip(request)):
        raise HTTPException(status_code=429, detail="Muitas tentativas. Aguarde alguns minutos e tente de novo.")


def _erro(exc: Exception, request: Request | None = None) -> HTTPException:
    if isinstance(exc, link_assinatura.LinkNaoEncontrado) and request is not None:
        rate_limit.registrar_falha(_chave_ip(request))
    if isinstance(exc, link_assinatura.LinkInvalido):
        return HTTPException(status_code=410, detail=str(exc))
    if isinstance(exc, link_assinatura.CpfIncorreto):
        restantes = exc.tentativas_restantes
        detalhe = (
            f"Os dígitos do CPF não conferem. Você tem mais {restantes} tentativa(s)."
            if restantes > 0
            else "Os dígitos do CPF não conferem e o link foi bloqueado. Peça um novo à equipe."
        )
        return HTTPException(status_code=403, detail=detalhe)
    if isinstance(exc, service.ContratoJaAssinado):
        return HTTPException(status_code=409, detail="Este contrato já foi assinado.")
    if isinstance(exc, Base64Invalido):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, service.ContratoDadosIncompletos):
        return HTTPException(status_code=422, detail=str(exc))
    raise exc


@router.get("/{token}")
def situacao_link(token: str, request: Request, db: Session = Depends(get_db)) -> dict:
    """Só diz se o link ainda é utilizável (sem nenhum dado pessoal) — o
    frontend usa pra mostrar o campo de CPF ou o motivo da recusa."""
    _freio_ip(request)
    try:
        link = link_assinatura.validar_link(db, token)
    except link_assinatura.LinkInvalido as exc:
        raise _erro(exc, request) from exc
    return {"valido": True, "expira_em": link.expira_em}


@router.post("/{token}/verificar", response_model=AssinaturaPublicaResumo)
def verificar(token: str, dados: AssinaturaPublicaCpf, request: Request, db: Session = Depends(get_db)) -> dict:
    _freio_ip(request)
    try:
        return link_assinatura.resumo_contrato(db, token, dados.cpf_final)
    except (link_assinatura.LinkInvalido, link_assinatura.CpfIncorreto) as exc:
        raise _erro(exc, request) from exc


@router.post("/{token}/previa")
def previa(token: str, dados: AssinaturaPublicaCpf, request: Request, db: Session = Depends(get_db)) -> Response:
    _freio_ip(request)
    try:
        conteudo = link_assinatura.pdf_previa(db, token, dados.cpf_final)
    except (link_assinatura.LinkInvalido, link_assinatura.CpfIncorreto) as exc:
        raise _erro(exc, request) from exc
    return Response(content=conteudo, media_type="application/pdf")


@router.post("/{token}/assinar", status_code=201)
def assinar(token: str, dados: AssinaturaPublicaAssinar, request: Request, db: Session = Depends(get_db)) -> dict:
    _freio_ip(request)
    try:
        contrato = link_assinatura.assinar(db, token, dados.cpf_final, dados.assinatura_png_base64)
    except (
        link_assinatura.LinkInvalido,
        link_assinatura.CpfIncorreto,
        service.ContratoJaAssinado,
        service.ContratoDadosIncompletos,
        Base64Invalido,
    ) as exc:
        raise _erro(exc, request) from exc
    return {"assinado": True, "data_assinatura": contrato.data_assinatura}
