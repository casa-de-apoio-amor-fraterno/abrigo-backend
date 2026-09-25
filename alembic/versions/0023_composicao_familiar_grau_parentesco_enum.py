"""Normaliza grau_parentesco de composicao_familiar pra lista fechada

`composicao_familiar.grau_parentesco` era texto livre (varchar(60)) — no
dump de produção existem ~90 variações distintas depois de normalizar
case/espaços: erros de digitação ("espoosa", "padastro"), sinônimos
("marido"/"esposo", "genitora"/"mãe"), valores compostos ("filho/enteado",
"marido/Dirlane" — esse último com nome de pessoa colado no valor) e
placeholders/lixo que não são parentesco de fato ("----", ".", "vizinho",
"casada", "amiga"). Decisão do time: substituir a coluna em vez de manter
o texto livre numa coluna paralela (diferente do padrão usado em
`estadia.tempo_estadia`, migração 0017) — cada linha recebe o valor
correspondente de `GrauParentesco` (`app/features/composicao_familiar/
models.py`), com `Outro` como fallback pra tudo que não bate com nenhuma
variação conhecida (inclusive dado futuro imprevisto, via o `ELSE` do
`CASE`).

O mapeamento completo foi construído a partir do dado real (consulta
`SELECT DISTINCT lower(trim(grau_parentesco))` no dump de produção,
2026-09-25) — cobre as ~90 variações observadas; não é uma tentativa de
adivinhar valores não vistos.

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-25

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

# valor canônico (GrauParentesco.value) -> variações reais observadas,
# já em lower(trim(...)) pra bater com a normalização do WHERE abaixo.
_MAPA: dict[str, list[str]] = {
    "Pai": ["pai", "genitor"],
    "Mãe": [
        "mae",
        "mãe",
        "genitora",
        "gernitora",  # erro de digitação de "genitora"
        "mãe de criação",
        "mãe/sogra",  # valor composto — mantém a primeira relação citada
        "genitora de jessica bona",  # nome de outra pessoa colado no valor
    ],
    "Filho": ["filho", "filho/enteado", "filho/neto"],
    "Filha": [
        "filha",
        "filha adotiva",
        "filha cuidadora",
        "filha de criação",
        "filha/enteada",
        "filha/neta",
    ],
    "Esposo": ["esposo", "marido", "marido/dirlane"],
    "Esposa": ["esposa", "espoosa", "esposa/nora"],
    "Companheiro": ["companheiro"],
    "Companheira": ["companheira"],
    "Namorado": ["namorado"],
    "Namorada": ["namorada"],
    "Irmão": ["irmão"],
    "Irmã": ["irma", "irmã"],
    "Avô": ["avô"],
    # "avo" sem acento é ambíguo (avô/avó) — "avó" é disparadamente mais
    # comum no resto do dado real (14+2 contra 2), assumido como o caso
    # mais provável pro único registro sem acento.
    "Avó": ["avó", "avo"],
    "Bisavô": [],
    "Bisavó": ["bisavó"],
    "Neto": ["neto", "neto/filho"],
    "Neta": ["neta"],
    "Bisneto": ["bisneto"],
    "Bisneta": ["bisneta"],
    "Genro": ["genro"],
    "Nora": ["nora"],
    "Sogro": ["sogro"],
    "Sogra": ["sogra"],
    "Cunhado": ["cunhado"],
    "Cunhada": ["cunhada"],
    "Tio": ["tio"],
    "Tia": ["tia"],
    "Sobrinho": ["sobrinho"],
    "Sobrinha": ["sobrinha"],
    "Primo": ["primo"],
    "Prima": ["prima"],
    "Enteado": ["enteado"],
    "Enteada": ["enteada", "enteadaa"],  # "enteadaa" é erro de digitação
    "Padrasto": ["padrasto", "padastro", "padrastro"],
    "Madrasta": ["madastra"],
    "Cuidador": ["cuidador"],
    "Cuidadora": ["cuidadora"],
    "Responsável": ["responsavel", "responsável"],
    # Placeholders/lixo ("----", ".", "===" etc.), status civil preenchido
    # no campo errado ("casada"/"casado"/"solteiro"), relações ambíguas de
    # gênero ("conjuge") ou que não são parentesco de fato
    # ("vizinho"/"amiga"), e casos compostos ambíguos demais pra escolher
    # um lado ("esposo da cuidora", "marido da sobrinha", "sobrinha
    # neta", "ex-marido").
    "Outro": [
        "",
        "-",
        "--",
        "---",
        "----",
        "-----",
        "------",
        "-------",
        "--------",
        ".",
        "......",
        "==-",
        "===",
        "====",
        "=====",
        "0---",
        "0----",
        "hfh",
        "vizinho",
        "amiga",
        "casada",
        "casado",
        "solteiro",
        "conjuge",
        "esposo da cuidora",
        "marido da sobrinha",
        "sobrinha neta",
        "ex-marido",
    ],
}


def upgrade() -> None:
    for valor, variacoes in _MAPA.items():
        if not variacoes:
            continue
        op.execute(
            sa.text(
                "UPDATE composicao_familiar SET grau_parentesco = :valor "
                "WHERE lower(trim(grau_parentesco)) IN :variacoes"
            )
            .bindparams(sa.bindparam("variacoes", expanding=True))
            .bindparams(valor=valor, variacoes=variacoes)
        )

    # Rede de segurança pra qualquer variação real não coberta no mapa
    # acima (não deveria sobrar nenhuma, já que o mapa foi construído a
    # partir do `SELECT DISTINCT` do dado de produção, mas garante que a
    # coluna nunca fique com um valor fora da lista de `GrauParentesco`).
    todas_variacoes = [v for variacoes in _MAPA.values() for v in variacoes]
    op.execute(
        sa.text(
            "UPDATE composicao_familiar SET grau_parentesco = 'Outro' "
            "WHERE lower(trim(grau_parentesco)) NOT IN :variacoes"
        )
        .bindparams(sa.bindparam("variacoes", expanding=True))
        .bindparams(variacoes=todas_variacoes)
    )


def downgrade() -> None:
    # Irreversível por natureza — normaliza ~90 variações de texto livre
    # pra uma lista fechada, o texto original não é preservado em nenhuma
    # coluna paralela (decisão do time, ver docstring). Mesmo padrão de
    # 0018 (correções de dados não têm downgrade).
    pass
