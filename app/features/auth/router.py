from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth import service
from app.features.auth.schemas import LoginRequest, SessaoResponse

router = APIRouter()


@router.post("/login", response_model=SessaoResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)) -> SessaoResponse:
    try:
        usuario = service.autenticar(db, dados.usuario, dados.senha)
    except service.CredenciaisInvalidas as exc:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos") from exc

    nome, token = service.gerar_sessao(usuario)
    return SessaoResponse(nome=nome, token=token)
