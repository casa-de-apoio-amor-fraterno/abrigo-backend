import io

from PIL import Image


def _png_valido(cor: tuple[int, int, int] = (255, 0, 0), tamanho: tuple[int, int] = (400, 300)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", tamanho, cor).save(buffer, format="PNG")
    return buffer.getvalue()


def _criar_material(client, descricao: str = "Cadeira de rodas") -> int:
    resposta = client.post(
        "/api/materiais",
        json={"descricao": descricao, "situacao": "Disponível", "local": "Casa"},
    )
    return resposta.json()["id"]


def test_material_sem_foto_tem_tem_foto_falso(client):
    material_id = _criar_material(client)

    resposta = client.get(f"/api/materiais/{material_id}")

    assert resposta.json()["tem_foto"] is False


def test_obter_foto_inexistente_retorna_404(client):
    material_id = _criar_material(client)

    assert client.get(f"/api/materiais/{material_id}/foto").status_code == 404
    assert client.get(f"/api/materiais/{material_id}/foto/thumb").status_code == 404


def test_salvar_e_obter_foto_e_thumb(client):
    material_id = _criar_material(client)
    conteudo = _png_valido()

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.png", conteudo, "image/png")},
    )
    assert resposta.status_code == 200
    assert resposta.json()["tem_foto"] is True

    resposta_foto = client.get(f"/api/materiais/{material_id}/foto")
    assert resposta_foto.status_code == 200
    assert resposta_foto.headers["content-type"] == "image/png"
    assert resposta_foto.content == conteudo

    resposta_thumb = client.get(f"/api/materiais/{material_id}/foto/thumb")
    assert resposta_thumb.status_code == 200
    assert resposta_thumb.headers["content-type"] == "image/png"
    assert resposta_thumb.content != conteudo  # a miniatura é um arquivo menor, redimensionado

    thumb = Image.open(io.BytesIO(resposta_thumb.content))
    assert thumb.width <= 200
    assert thumb.height <= 200


def test_salvar_foto_formato_nao_suportado(client):
    material_id = _criar_material(client)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.gif", b"abc", "image/gif")},
    )

    assert resposta.status_code == 400


def test_salvar_foto_conteudo_nao_e_imagem_valida(client):
    """Content-type declarado bate com a whitelist, mas o conteúdo não é
    uma imagem de verdade (arquivo corrompido ou content-type forjado)."""
    material_id = _criar_material(client)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.jpg", b"isto nao e uma imagem", "image/jpeg")},
    )

    assert resposta.status_code == 400


def test_salvar_foto_maior_que_limite(client):
    material_id = _criar_material(client)
    conteudo_grande = b"a" * (5 * 1024 * 1024 + 1)

    resposta = client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.jpg", conteudo_grande, "image/jpeg")},
    )

    assert resposta.status_code == 400


def test_remover_foto(client):
    material_id = _criar_material(client)
    client.put(
        f"/api/materiais/{material_id}/foto",
        files={"arquivo": ("foto.png", _png_valido(), "image/png")},
    )

    resposta = client.delete(f"/api/materiais/{material_id}/foto")
    assert resposta.status_code == 204

    resposta = client.get(f"/api/materiais/{material_id}")
    assert resposta.json()["tem_foto"] is False
    assert client.get(f"/api/materiais/{material_id}/foto/thumb").status_code == 404
