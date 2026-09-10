"""Cria (ou redefine a senha de) um usuário direto no banco.

Uso:
    python -m app.scripts.criar_usuario <login> <senha> "<nome>" [perfil]

Não existe endpoint de cadastro de usuário exposto pela API — usuários são
criados/gerenciados pela equipe técnica. Este script grava já em
`senha_hash` (bcrypt), sem passar pelo campo legado `senha`.
"""

import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_senha
from app.features.usuarios.models import Usuario


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(1)

    login, senha, nome = sys.argv[1], sys.argv[2], sys.argv[3]
    perfil = sys.argv[4] if len(sys.argv) > 4 else None

    db = SessionLocal()
    try:
        usuario = db.scalar(select(Usuario).where(Usuario.login == login))
        if usuario is None:
            usuario = Usuario(login=login, nome=nome, perfil=perfil)
            db.add(usuario)
            acao = "criado"
        else:
            usuario.nome = nome
            usuario.perfil = perfil or usuario.perfil
            acao = "atualizado"

        usuario.senha_hash = hash_senha(senha)
        usuario.senha = None
        db.commit()
        print(f"Usuário '{login}' {acao} com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
