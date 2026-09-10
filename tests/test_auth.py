from app.features.usuarios.models import Usuario


def test_login_com_senha_legado_texto_plano(client, db_session, usuario_legado):
    resposta = client.post("/api/auth/login", json={"usuario": "joana", "senha": "123456"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Joana Assistente Social"
    assert corpo["token"]

    # migração oportunista: senha_hash preenchida, texto plano limpo
    usuario = db_session.get(Usuario, usuario_legado.id)
    assert usuario.senha_hash is not None
    assert usuario.senha is None


def test_login_com_senha_ja_migrada(client, usuario_migrado):
    resposta = client.post("/api/auth/login", json={"usuario": "carlos", "senha": "abc12345"})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Carlos Coordenador"


def test_login_senha_incorreta(client, usuario_legado):
    resposta = client.post("/api/auth/login", json={"usuario": "joana", "senha": "errada"})

    assert resposta.status_code == 401


def test_login_usuario_inexistente(client):
    resposta = client.post("/api/auth/login", json={"usuario": "ninguem", "senha": "123456"})

    assert resposta.status_code == 401
