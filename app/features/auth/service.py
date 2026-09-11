from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import criar_token_acesso, hash_senha, verificar_senha
from app.features.usuarios.models import Usuario


class CredenciaisInvalidas(Exception):
    pass


def autenticar(db: Session, login: str, senha: str) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.login == login))
    if usuario is None:
        raise CredenciaisInvalidas

    # Correção deliberada em relação ao legado: untFrmLogin.pas nunca checava
    # `ativo` — um usuário desativado ainda conseguia logar. Ver usuario.legacy.md.
    if not usuario.ativo:
        raise CredenciaisInvalidas

    if usuario.senha_hash:
        if not verificar_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidas
    else:
        # Compatibilidade com o sistema legado: senha em texto plano.
        # Ver app/features/usuarios/usuario.legacy.md.
        if usuario.senha != senha:
            raise CredenciaisInvalidas

        usuario.senha_hash = hash_senha(senha)
        usuario.senha = None
        db.commit()
        db.refresh(usuario)

    return usuario


def gerar_sessao(usuario: Usuario) -> tuple[str, str, str, int]:
    token = criar_token_acesso(usuario.id)
    return usuario.nome, token, usuario.perfil, usuario.id
