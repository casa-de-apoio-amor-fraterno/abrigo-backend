import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_senha
from app.features.usuarios.models import Usuario
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def usuario_legado(db_session) -> Usuario:
    """Usuário com senha em texto plano, como no sistema legado."""
    usuario = Usuario(login="joana", nome="Joana Assistente Social", perfil="assistente_social", senha="123456")
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture()
def usuario_inativo(db_session) -> Usuario:
    """Usuário desativado — não deve conseguir logar (correção em relação ao legado)."""
    usuario = Usuario(
        login="thiago",
        nome="Thiago",
        perfil="geral",
        senha="plantonista",
        ativo=False,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture()
def usuario_migrado(db_session) -> Usuario:
    """Usuário que já logou uma vez no sistema novo (senha_hash preenchida)."""
    usuario = Usuario(
        login="carlos",
        nome="Carlos Coordenador",
        perfil="coordenador",
        senha=None,
        senha_hash=hash_senha("abc12345"),
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario
