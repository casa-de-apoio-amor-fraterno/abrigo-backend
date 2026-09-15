import io

from PIL import Image

from app.core.security import criar_token_acesso


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def _png_valido(cor: tuple[int, int, int] = (255, 0, 0), tamanho: tuple[int, int] = (400, 300)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", tamanho, cor).save(buffer, format="PNG")
    return buffer.getvalue()


def _criar_material(client, headers: dict, descricao: str = "Cadeira de rodas") -> int:
    resposta = client.post(
        "/api/materiais",
        json={"descricao": descricao, "situacao": "Disponível", "local": "Casa"},
        headers=headers,
    )
    return resposta.json()["id"]


def test_material_sem_foto_tem_tem_foto_falso(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)

    resposta = client.get(f"/api/materiais/{material_id}", headers=headers)

    assert resposta.json()["tem_foto"] is False


def test_obter_foto_inexistente_retorna_404(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)

    assert client.get(f"/api/materiais/{material_id}/foto", headers=headers).status_code == 404
    assert client.get(f"/api/materiais/{material_id}/foto/thumb", headers=headers).status_code == 404


def test_salvar_e_obter_foto_e_thumb(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)
    conteudo = _png_valido()

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.png", conteudo, "image/png")},
        headers=headers,
    )
    assert resposta.status_code == 200
    assert resposta.json()["tem_foto"] is True

    resposta_foto = client.get(f"/api/materiais/{material_id}/foto", headers=headers)
    assert resposta_foto.status_code == 200
    assert resposta_foto.headers["content-type"] == "image/png"
    assert resposta_foto.content == conteudo

    resposta_thumb = client.get(f"/api/materiais/{material_id}/foto/thumb", headers=headers)
    assert resposta_thumb.status_code == 200
    assert resposta_thumb.headers["content-type"] == "image/png"
    assert resposta_thumb.content != conteudo  # a miniatura é um arquivo menor, redimensionado

    thumb = Image.open(io.BytesIO(resposta_thumb.content))
    assert thumb.width <= 200
    assert thumb.height <= 200


def test_salvar_foto_formato_nao_suportado(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.gif", b"abc", "image/gif")},
        headers=headers,
    )

    assert resposta.status_code == 400


def test_salvar_foto_conteudo_nao_e_imagem_valida(client, usuario_legado):
    """Content-type declarado bate com a whitelist, mas o conteúdo não é
    uma imagem de verdade (arquivo corrompido ou content-type forjado)."""
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.jpg", b"isto nao e uma imagem", "image/jpeg")},
        headers=headers,
    )

    assert resposta.status_code == 400


def test_salvar_foto_maior_que_limite(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)
    conteudo_grande = b"a" * (5 * 1024 * 1024 + 1)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.jpg", conteudo_grande, "image/jpeg")},
        headers=headers,
    )

    assert resposta.status_code == 400


def test_remover_foto(client, usuario_legado):
    headers = _auth_header(usuario_legado)
    material_id = _criar_material(client, headers)
    client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.png", _png_valido(), "image/png")},
        headers=headers,
    )

    resposta = client.delete(f"/api/materiais/{material_id}/foto", headers=headers)
    assert resposta.status_code == 204

    resposta = client.get(f"/api/materiais/{material_id}", headers=headers)
    assert resposta.json()["tem_foto"] is False
    assert client.get(f"/api/materiais/{material_id}/foto/thumb", headers=headers).status_code == 404
