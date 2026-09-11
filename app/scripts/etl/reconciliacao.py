"""Reconciliação de `acompanhamento` (tabela legada antiga, sem FK real —
ver achado 1 de `docs/atividades.md`) em `estadia_acompanhante` (tabela
nova, mantida — ver `app/features/estadias/estadia.legacy.md`).

`acompanhamento` só tem `id_paciente`/`id_acompanhante`, sem data — não dá
pra saber com certeza a qual `estadia` do paciente cada registro se refere
quando o paciente teve mais de uma estadia. Decisão: só reconciliar de
forma automática quando o paciente teve exatamente UMA estadia (caso
inambíguo); os demais ficam pendentes de revisão manual, listados à parte
— não descartados silenciosamente.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistroAcompanhamento:
    id_acompanhamento: int
    id_paciente: int
    id_acompanhante: int


@dataclass(frozen=True)
class ResultadoReconciliacao:
    reconciliados: list[dict]
    """Registros prontos pra virar `EstadiaAcompanhante`: {id_estadia, id_pessoa}."""

    pendentes_revisao_manual: list[RegistroAcompanhamento]
    """`acompanhamento` que não deu pra reconciliar sozinho (0 ou 2+
    estadias pro paciente) — precisam de decisão humana, não de heurística."""


def reconciliar(
    registros: list[RegistroAcompanhamento],
    estadias_por_pessoa: dict[int, list[int]],
) -> ResultadoReconciliacao:
    """`estadias_por_pessoa`: mapa `id_pessoa -> [id_estadia, ...]` (todas
    as estadias em que essa pessoa é a `id_pessoa`, isto é, a paciente)."""

    reconciliados: list[dict] = []
    pendentes: list[RegistroAcompanhamento] = []

    for registro in registros:
        estadias_do_paciente = estadias_por_pessoa.get(registro.id_paciente, [])
        if len(estadias_do_paciente) == 1:
            reconciliados.append(
                {"id_estadia": estadias_do_paciente[0], "id_pessoa": registro.id_acompanhante}
            )
        else:
            pendentes.append(registro)

    return ResultadoReconciliacao(reconciliados=reconciliados, pendentes_revisao_manual=pendentes)
