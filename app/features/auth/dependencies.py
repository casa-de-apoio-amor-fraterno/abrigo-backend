from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token
from app.features.usuarios.models import Usuario

_esquema_bearer = HTTPBearer(auto_error=False)


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciais is None:
        raise HTTPException(status_code=401, detail="Não autenticado")

    usuario_id = decodificar_token(credenciais.credentials)
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário inválido")

    return usuario


def usuario_atual_opcional(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Como `usuario_atual`, mas devolve `None` em vez de 401 quando não há
    sessão — pra endpoints que normalmente não exigem login, mas precisam
    saber quem é o usuário (se houver) pra decidir algo pontual (ver
    `criar` em app/features/pessoas/router.py, que só checa perfil quando
    o payload inclui composição familiar aninhada)."""
    if credenciais is None:
        return None

    usuario_id = decodificar_token(credenciais.credentials)
    if usuario_id is None:
        return None

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        return None

    return usuario


def exigir_perfil(*perfis: str):
    """Dependência que restringe um endpoint a um ou mais `Usuario.perfil`.

    Regra nova — o legado (Delphi) não implementava nenhum controle de
    acesso por perfil; qualquer usuário logado via `untFrmLogin` conseguia
    abrir qualquer tela, incluindo avaliação social e composição familiar
    (dados sensíveis). Ver `app/features/pessoas/pessoa.legacy.md`.
    """

    def verificador(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(status_code=403, detail="Acesso restrito a este perfil")
        return usuario

    return verificador
