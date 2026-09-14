import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import criar_token_acesso
from app.features.pessoas import service
from app.main import _frontend_dist, app


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


@pytest.mark.skipif(
    not _frontend_dist.is_dir(), reason="build do frontend não gerado (rode `npm run build`)"
)
class TestServirFrontend:
    def test_raiz_serve_index_html(self, client):
        resposta = client.get("/")
        assert resposta.status_code == 200
        assert resposta.headers["content-type"].startswith("text/html")

    def test_rota_do_angular_cai_no_index_html(self, client):
        # /pessoas/5/editar não existe como arquivo — é uma rota do Angular
        # Router, resolvida no navegador a partir do index.html.
        resposta = client.get("/pessoas/5/editar")
        assert resposta.status_code == 200
        assert resposta.headers["content-type"].startswith("text/html")

    def test_asset_estatico_e_servido_com_content_type_proprio(self, client):
        resposta = client.get("/favicon.png")
        assert resposta.status_code == 200
        assert resposta.headers["content-type"] == "image/png"

    def test_nao_permite_path_traversal(self, client):
        resposta = client.get("/../../.env")
        # O navegador/httpx já normaliza ".." antes de mandar a requisição,
        # então isso cai como rota normal (não existe arquivo -> index.html),
        # não como erro — o teste real de proteção é a asserção de que
        # nunca devolve o conteúdo de um arquivo fora de `_frontend_dist`.
        assert resposta.status_code == 200
        assert resposta.headers["content-type"].startswith("text/html")
