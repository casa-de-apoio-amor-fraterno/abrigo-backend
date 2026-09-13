from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.database import get_db
from app.features.auth import service
from app.features.auth.schemas import LoginRequest, SessaoResponse

router = APIRouter()


@router.post("/login", response_model=SessaoResponse)
def login(dados: LoginRequest, request: Request, db: Session = Depends(get_db)) -> SessaoResponse:
    chave = (request.client.host if request.client else "desconhecido", dados.usuario)

    if rate_limit.limite_excedido(chave):
        raise HTTPException(
            status_code=429, detail="Muitas tentativas de login. Tente novamente mais tarde."
        )

    try:
        usuario = service.autenticar(db, dados.usuario, dados.senha)
    except service.CredenciaisInvalidas as exc:
        rate_limit.registrar_falha(chave)
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos") from exc

    rate_limit.limpar(chave)
    nome, token, perfil, usuario_id = service.gerar_sessao(usuario)
    return SessaoResponse(nome=nome, token=token, perfil=perfil, usuario_id=usuario_id)
