"""ETL do MySQL legado (`sgf_abrigo`, MySQL 5.5) pro Postgres novo.

Uso:
    python -m app.scripts.etl_migracao --mysql-url mysql+pymysql://usuario:senha@host/sgf_abrigo [--confirmar]

Sem `--confirmar`, roda em modo dry-run: conecta nas duas bases, lê e
transforma cada tabela, mas não grava nada no Postgres — só imprime quantas
linhas seriam inseridas por tabela.

Pré-requisitos (ver docs/migracao-postgres.md):
1. NUNCA rodar contra o dump/produção diretamente na primeira tentativa.
   Restaurar o dump `sgf_abrigo*.sql` num MySQL local descartável primeiro,
   e apontar `--mysql-url` pra ele.
2. Rodar `alembic upgrade head` no Postgres alvo (schema vazio) antes deste
   script — ele só insere linhas, não cria tabelas.
3. Depois de rodar com `--confirmar`, rodar
   `python -m app.scripts.hash_senhas_pendentes --confirmar` (senha de
   usuário migra em texto plano, ver `transformacoes.transformar_usuario`).
4. Validar contagens de linha e uma amostra de registros antes de repetir
   contra o dump/produção real, num Postgres definitivo.

Este script foi escrito em Python (SQLAlchemy + pymysql pra ler o MySQL,
o `SessionLocal` da própria aplicação pra escrever no Postgres) no lugar de
pgloader — decisão registrada em docs/migracao-postgres.md: o ambiente onde
este projeto foi desenvolvido não tinha pgloader disponível, e a lógica de
transformação por tabela (datas zeradas, Sim/Não -> boolean, reconciliação
de `acompanhamento`) é mais fácil de escrever e testar em Python puro
(ver tests/test_etl_transformacoes.py e tests/test_etl_reconciliacao.py)
do que na DSL do pgloader.

A ordem de carga segue o mapa de FKs de docs/atividades.md: tabelas sem
dependência primeiro, depois `municipio` (depende de `estado`), `pessoa`
(depende de `estado`/`municipio`/`hospital`), `estadia` (depende de
`pessoa`/`quarto`/`usuario`), e por fim o que depende de `estadia`.
"""

import argparse
import sys
from collections.abc import Callable

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal
from app.features.avaliacao_social.models import AvaliacaoSocial
from app.features.composicao_familiar.models import ComposicaoFamiliar
from app.features.emprestimos.models import Emprestimo, EmprestimoItem
from app.features.estadias.models import Estadia, EstadiaAcompanhante
from app.features.estados.models import Estado
from app.features.hospitais.models import Hospital
from app.features.materiais.models import Material
from app.features.municipios.models import Municipio
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.usuarios.models import Usuario
from app.features.voluntarios.models import Voluntario
from app.scripts.etl import transformacoes as t
from app.scripts.etl.reconciliacao import RegistroAcompanhamento, reconciliar


def _ler_tabela(conexao_origem, tabela: str) -> list[dict]:
    resultado = conexao_origem.execute(text(f"SELECT * FROM `{tabela}`"))
    return [dict(linha._mapping) for linha in resultado]


def _carregar_tabela(
    conexao_origem,
    sessao_destino: Session,
    tabela_origem: str,
    transformar: Callable[[dict], dict],
    modelo_destino: type[Base],
    confirmar: bool,
) -> int:
    linhas = _ler_tabela(conexao_origem, tabela_origem)
    transformadas = [transformar(linha) for linha in linhas]

    print(f"  {tabela_origem} -> {modelo_destino.__tablename__}: {len(transformadas)} linha(s)")

    if confirmar and transformadas:
        sessao_destino.bulk_insert_mappings(modelo_destino, transformadas)
        sessao_destino.commit()

    return len(transformadas)


def _reconciliar_acompanhamento(
    conexao_origem, sessao_destino: Session, confirmar: bool
) -> None:
    registros_acompanhamento = [
        RegistroAcompanhamento(
            id_acompanhamento=linha["id_acompanhamento"],
            id_paciente=linha["id_paciente"],
            id_acompanhante=linha["id_acompanhante"],
        )
        for linha in _ler_tabela(conexao_origem, "acompanhamento")
    ]

    estadias = _ler_tabela(conexao_origem, "estadia")
    estadias_por_pessoa: dict[int, list[int]] = {}
    data_entrada_por_estadia: dict[int, object] = {}
    for estadia in estadias:
        estadias_por_pessoa.setdefault(estadia["id_pessoa"], []).append(estadia["id_estadia"])
        data_entrada_por_estadia[estadia["id_estadia"]] = t.datetime_zerado_para_none(
            estadia["data_entrada"]
        )

    resultado = reconciliar(registros_acompanhamento, estadias_por_pessoa)

    # `acompanhamento` não guarda data — usa a `data_entrada` da própria
    # estadia do paciente como aproximação (documentado em
    # app/features/estadias/estadia.legacy.md), já que
    # `EstadiaAcompanhante.data_entrada` é obrigatória.
    for reconciliado in resultado.reconciliados:
        reconciliado["data_entrada"] = data_entrada_por_estadia.get(reconciliado["id_estadia"])

    print(
        f"  acompanhamento -> estadia_acompanhante (reconciliado): "
        f"{len(resultado.reconciliados)} linha(s); "
        f"{len(resultado.pendentes_revisao_manual)} pendente(s) de revisão manual"
    )
    if resultado.pendentes_revisao_manual:
        print("  Pendentes (paciente com 0 ou 2+ estadias — não reconciliado automaticamente):")
        for pendente in resultado.pendentes_revisao_manual:
            print(
                f"    - acompanhamento.id={pendente.id_acompanhamento} "
                f"(paciente={pendente.id_paciente}, acompanhante={pendente.id_acompanhante})"
            )

    if confirmar and resultado.reconciliados:
        # Sem `id` explícito: são linhas sintéticas, não existem em
        # `estadia_acompanhante` no legado — deixa o Postgres atribuir o id.
        sessao_destino.bulk_insert_mappings(EstadiaAcompanhante, resultado.reconciliados)
        sessao_destino.commit()


TABELAS_SIMPLES: list[tuple[str, Callable[[dict], dict], type[Base]]] = [
    ("estado", t.transformar_estado, Estado),
    ("hospital", t.transformar_hospital, Hospital),
    ("usuario", t.transformar_usuario, Usuario),
    ("quarto", t.transformar_quarto, Quarto),
    ("voluntario", t.transformar_voluntario, Voluntario),
    ("material", t.transformar_material, Material),
    ("municipio", t.transformar_municipio, Municipio),
    ("pessoa", t.transformar_pessoa, Pessoa),
    ("estadia", t.transformar_estadia, Estadia),
    ("estadia_acompanhante", t.transformar_estadia_acompanhante, EstadiaAcompanhante),
    ("avaliacao_social", t.transformar_avaliacao_social, AvaliacaoSocial),
    ("composicao_familiar", t.transformar_composicao_familiar, ComposicaoFamiliar),
    ("emprestimo", t.transformar_emprestimo, Emprestimo),
    ("emprestimo_item", t.transformar_emprestimo_item, EmprestimoItem),
]


def executar(mysql_url: str, confirmar: bool) -> None:
    engine_origem = create_engine(mysql_url)
    sessao_destino = SessionLocal()

    try:
        with engine_origem.connect() as conexao_origem:
            print("Carregando tabelas (ordem respeita as FKs — ver docs/atividades.md):")
            for tabela_origem, transformar, modelo_destino in TABELAS_SIMPLES:
                _carregar_tabela(
                    conexao_origem, sessao_destino, tabela_origem, transformar, modelo_destino, confirmar
                )

            _reconciliar_acompanhamento(conexao_origem, sessao_destino, confirmar)

        if not confirmar:
            print(
                "\nModo dry-run — nada foi gravado no Postgres. Rode com --confirmar para aplicar."
            )
        else:
            print(
                "\nCarga concluída. Próximo passo: "
                "`python -m app.scripts.hash_senhas_pendentes --confirmar`."
            )
    finally:
        sessao_destino.close()
        engine_origem.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mysql-url",
        required=True,
        help="URL SQLAlchemy do MySQL de origem, ex.: mysql+pymysql://usuario:senha@localhost/sgf_abrigo",
    )
    parser.add_argument("--confirmar", action="store_true", help="Grava de verdade no Postgres alvo.")
    args = parser.parse_args()

    executar(args.mysql_url, args.confirmar)


if __name__ == "__main__":
    sys.exit(main())
