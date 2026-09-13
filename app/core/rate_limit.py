"""Limitador de tentativas simples, em memória, para o login.

Sem infraestrutura externa (Redis etc.) — adequado ao porte da aplicação
(instância única). Bloqueia por combinação (IP, usuário) depois de várias
falhas seguidas, não por IP isolado, para não travar todo mundo atrás do
mesmo NAT/proxy nem servir de vetor de DoS contra um usuário conhecido.
"""

import time
from collections import defaultdict
from threading import Lock

JANELA_SEGUNDOS = 15 * 60
MAX_TENTATIVAS = 5

_falhas: dict[tuple[str, str], list[float]] = defaultdict(list)
_lock = Lock()


def _tentativas_na_janela(chave: tuple[str, str], agora: float) -> list[float]:
    return [t for t in _falhas.get(chave, []) if agora - t < JANELA_SEGUNDOS]


def limite_excedido(chave: tuple[str, str]) -> bool:
    agora = time.monotonic()
    with _lock:
        tentativas = _tentativas_na_janela(chave, agora)
        _falhas[chave] = tentativas
        return len(tentativas) >= MAX_TENTATIVAS


def registrar_falha(chave: tuple[str, str]) -> None:
    agora = time.monotonic()
    with _lock:
        tentativas = _tentativas_na_janela(chave, agora)
        tentativas.append(agora)
        _falhas[chave] = tentativas


def limpar(chave: tuple[str, str]) -> None:
    with _lock:
        _falhas.pop(chave, None)
