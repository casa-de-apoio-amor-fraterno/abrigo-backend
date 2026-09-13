from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import criar_token_acesso
from app.features.pessoas import service
from app.main import app


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def test_excecao_nao_tratada_retorna_500_generico(db_session, usuario_legado, monkeypatch):
    def _levanta(*args, **kwargs):
        raise RuntimeError("detalhe interno que não deveria vazar")

    monkeypatch.setattr(service, "listar", _levanta)

    app.dependency_overrides[get_db] = lambda: (yield db_session)
    try:
        # raise_server_exceptions=False: por padrão o TestClient relança a
        # exceção original pra debug, mascarando o comportamento real do
        # handler — aqui queremos testar a resposta HTTP de verdade.
        with TestClient(app, raise_server_exceptions=False) as client:
            resposta = client.get("/api/pessoas", headers=_auth_header(usuario_legado))
    finally:
        app.dependency_overrides.clear()

    assert resposta.status_code == 500
    assert resposta.json() == {"detail": "Erro interno do servidor"}
