"""Hasheia em massa toda senha em texto plano ainda pendente na tabela `usuario`.

Uso:
    python -m app.scripts.hash_senhas_pendentes [--confirmar]

Sem `--confirmar`, roda em modo dry-run: só lista quantos usuários seriam
afetados, sem gravar nada.

Por quê: o login (`app/features/auth/service.py`) já migra a senha de texto
plano pra hash sozinho, mas só quando o usuário loga pela primeira vez no
sistema novo — até lá, a senha continua em texto plano no banco. Rodar este
script logo após o ETL do MySQL legado (ver docs/migracao-postgres.md)
elimina esse texto plano de uma vez, sem depender de cada usuário logar.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_senha
from app.features.usuarios.models import Usuario


def listar_pendentes(db: Session) -> list[Usuario]:
    return list(
        db.scalars(select(Usuario).where(Usuario.senha_hash.is_(None), Usuario.senha.is_not(None))).all()
    )


def hashear(db: Session, usuarios: list[Usuario]) -> None:
    for usuario in usuarios:
        usuario.senha_hash = hash_senha(usuario.senha)
        usuario.senha = None
    db.commit()


def main() -> None:
    confirmar = "--confirmar" in sys.argv

    db = SessionLocal()
    try:
        pendentes = listar_pendentes(db)

        if not pendentes:
            print("Nenhuma senha em texto plano pendente.")
            return

        print(f"{len(pendentes)} usuário(s) com senha em texto plano:")
        for usuario in pendentes:
            print(f"  - {usuario.login} (id {usuario.id})")

        if not confirmar:
            print("\nModo dry-run — nada foi alterado. Rode com --confirmar para aplicar.")
            return

        hashear(db, pendentes)
        print(f"\n{len(pendentes)} senha(s) hasheada(s) e texto plano removido.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
