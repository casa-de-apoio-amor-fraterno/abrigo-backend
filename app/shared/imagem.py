"""Utilidades pra lidar com imagens recebidas como base64 (assinatura por
toque/caneta, capturada no frontend via canvas — ver `shared/ui/assinatura-
canvas` no Angular)."""

from base64 import b64decode
from binascii import Error as Base64Error


class Base64Invalido(Exception):
    pass


def decodificar_base64_imagem(valor: str) -> bytes:
    """Aceita tanto a string base64 crua quanto uma data URL completa
    (`data:image/png;base64,....`, formato que `HTMLCanvasElement.
    toDataURL()` produz no frontend)."""
    base64_puro = valor.split(",")[-1]
    try:
        return b64decode(base64_puro, validate=True)
    except (Base64Error, ValueError) as exc:
        # ValueError: caracteres fora de ASCII (b64decode não aceita nem
        # tenta antes de validar o alfabeto base64) — Base64Error: alfabeto
        # válido só em ASCII, mas padding/conteúdo incorretos.
        raise Base64Invalido("Imagem em base64 inválida") from exc
