"""Funções puras de transformação de linhas do MySQL legado (`sgf_abrigo`)
para o formato aceito pelos models novos (Postgres).

Isoladas de qualquer conexão de banco de propósito — recebem e devolvem
`dict`, o que permite testar cada regra de conversão sem MySQL nem Postgres
reais rodando. A orquestração de leitura/escrita fica em
`app/scripts/etl_migracao.py`.

Ver `docs/migracao-postgres.md` e `docs/atividades.md` (achado 4) para o
raciocínio por trás de cada conversão.
"""

from datetime import date, datetime


def sim_nao_para_bool(valor: str | None) -> bool | None:
    """Converte o padrão legado `varchar(3)` 'Sim'/'Não' pra `bool`.

    Qualquer coisa que não seja exatamente 'Sim' (case-insensitive, com
    espaços nas pontas — o dado real tem valores como `'APMI '`) vira
    `False`; `None`/string vazia permanece `None` — ver achado 4 de
    `docs/atividades.md`.
    """
    if valor is None:
        return None
    valor_normalizado = valor.strip()
    if not valor_normalizado:
        return None
    return valor_normalizado.lower() == "sim"


def data_zerada_para_none(valor: str | date | datetime | None) -> date | None:
    """Trata a data zerada do MySQL (`'0000-00-00'`), que não existe no
    Postgres — mapeada pra `NULL` (sentinela documentada, não uma data
    real). Ver docs/migracao-postgres.md.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        if valor == date(1, 1, 1) or valor.year == 0:
            return None
        return valor

    texto = valor.strip()
    if not texto or texto.startswith("0000-00-00"):
        return None
    return date.fromisoformat(texto[:10])


def datetime_zerado_para_none(valor: str | datetime | None) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        if valor.year == 0:
            return None
        return valor

    texto = valor.strip()
    if not texto or texto.startswith("0000-00-00"):
        return None
    return datetime.fromisoformat(texto)


def texto_ou_none(valor: str | None) -> str | None:
    """Normaliza string vazia pra `None` (o dump tem muitos `''` em vez de
    `NULL` em campos de texto livre) — sem alterar o conteúdo real (não
    faz `strip()`, pra não perder espaços que fazem parte do dado, como
    `'APMI '`)."""
    if valor is None:
        return None
    return valor if valor != "" else None


def transformar_estado(linha: dict) -> dict:
    return {"id": linha["id_estado"], "nome": linha["nome"], "uf": linha["uf"]}


def transformar_hospital(linha: dict) -> dict:
    return {
        "id": linha["id_hospital"],
        "nome": linha["nome"],
        "ativo": sim_nao_para_bool(linha["ativo"]),
    }


def transformar_municipio(linha: dict) -> dict:
    return {
        "id": linha["id_municipio"],
        "nome": linha["nome"],
        "id_estado": linha["id_estado"],
    }


def transformar_quarto(linha: dict) -> dict:
    return {
        "id": linha["id_quarto"],
        "descricao": texto_ou_none(linha["descricao"]),
        "numero": linha["numero"],
        "leito": linha["leito"],
        "ativo": sim_nao_para_bool(linha["ativo"]),
    }


def transformar_usuario(linha: dict) -> dict:
    """`senha` migra como texto plano — o backend já trata isso (login com
    migração preguiçosa pro hash). Rodar
    `python -m app.scripts.hash_senhas_pendentes --confirmar` logo depois
    do ETL pra não deixar texto plano no banco novo (ver
    docs/migracao-postgres.md)."""
    return {
        "id": linha["id_usuario"],
        "login": linha["login"],
        "nome": linha["nome"],
        "perfil": linha["perfil"],
        "ativo": sim_nao_para_bool(linha["ativo"]),
        "senha": texto_ou_none(linha["senha"]),
        "senha_hash": None,
    }


def transformar_pessoa(linha: dict) -> dict:
    """`tipo` **não é copiado** — descartado deliberadamente (ver
    `app/features/pessoas/pessoa.legacy.md`). É lido só pra apoiar a
    reconciliação de `acompanhamento` em `estadia_acompanhante`
    (`app/scripts/etl/reconciliacao.py`), não persistido em `Pessoa`."""
    return {
        "id": linha["id_pessoa"],
        "nome": linha["nome"],
        "data_nascimento": data_zerada_para_none(linha["data_nascimento"]),
        "rg": texto_ou_none(linha["rg"]),
        "cpf": texto_ou_none(linha["cpf"]),
        "profissao": texto_ou_none(linha["profissao"]),
        "cartao_sus": texto_ou_none(linha["cartao_sus"]),
        "endereco": texto_ou_none(linha["endereco"]),
        "ponto_referencia": texto_ou_none(linha["ponto_referencia"]),
        "telefone": texto_ou_none(linha["telefone"]),
        "id_hospital": linha["id_hospital"],
        "id_municipio": linha["id_municipio"],
        "id_estado": linha["id_estado"],
        "observacao": texto_ou_none(linha["observacao"]),
        "acompanhamento_social": texto_ou_none(linha["acompanhamento_social"]),
        "data_cadastro": data_zerada_para_none(linha["data_cadastro"]),
        "ativo": sim_nao_para_bool(linha["ativo"]),
    }


def transformar_voluntario(linha: dict) -> dict:
    return {
        "id": linha["id_voluntario"],
        "nome": linha["nome"],
        "telefone": linha["telefone"],
        "setor": texto_ou_none(linha["setor"]),
        "data_nascimento": data_zerada_para_none(linha["data_nascimento"]),
        "estado_civil": texto_ou_none(linha["estado_civil"]),
        "cpf": texto_ou_none(linha["cpf"]),
        "endereco": texto_ou_none(linha["endereco"]),
        "formacao": texto_ou_none(linha["formacao"]),
        "observacao": texto_ou_none(linha["observacao"]),
        "ativo": sim_nao_para_bool(linha["ativo"]),
    }


def transformar_material(linha: dict) -> dict:
    return {
        "id": linha["id_material"],
        "descricao": linha["descricao"],
        "codigo_identificacao": texto_ou_none(linha["codigo_identificacao"]),
        "disponivel_emprestimo": sim_nao_para_bool(linha["disponivel_emprestimo"]) or False,
        "situacao": linha["situacao"],
        "local": linha["local"],
        "observacao": texto_ou_none(linha["observacao"]),
        "ativo": sim_nao_para_bool(linha["ativo"]),
        "motivo_baixa": texto_ou_none(linha["motivo_baixa"]),
    }


def transformar_estadia(linha: dict) -> dict:
    return {
        "id": linha["id_estadia"],
        "id_pessoa": linha["id_pessoa"],
        "id_quarto": linha["id_quarto"],
        "id_usuario": linha["id_usuario"],
        "data_entrada": datetime_zerado_para_none(linha["data_entrada"]),
        "data_saida": datetime_zerado_para_none(linha["data_saida"]),
        "tempo_estadia": texto_ou_none(linha["tempo_estadia"]),
        "tipo_pessoa": linha["tipo_pessoa"] or "Paciente",
        "situacao": linha["situacao"],
        "observacao": texto_ou_none(linha["observacao"]),
        "ativo": sim_nao_para_bool(linha["ativo"]),
    }


def transformar_estadia_acompanhante(linha: dict) -> dict:
    return {
        "id": linha["id_estadia_acompanhante"],
        "id_estadia": linha["id_estadia"],
        "id_pessoa": linha["id_pessoa"],
        "data_entrada": datetime_zerado_para_none(linha["data_entrada"]),
        "data_saida": datetime_zerado_para_none(linha["data_saida"]),
        "grau_parentesco": texto_ou_none(linha["grau_parentesco"]),
    }


def transformar_emprestimo(linha: dict) -> dict:
    return {
        "id": linha["id_emprestimo"],
        "id_pessoa": linha["id_pessoa"],
        "id_usuario": linha["id_usuario"],
        "situacao": linha["situacao"],
        "numero_contrato": texto_ou_none(linha["numero_contrato"]),
        "observacao": texto_ou_none(linha["observacao"]),
        "ativo": sim_nao_para_bool(linha["ativo"]) if linha["ativo"] is not None else True,
    }


def transformar_emprestimo_item(linha: dict) -> dict:
    return {
        "id": linha["id_emprestimo_item"],
        "id_emprestimo": linha["id_emprestimo"],
        "id_material": linha["id_material"],
        "data_emprestimo": data_zerada_para_none(linha["data_emprestimo"]),
        "data_devolucao": data_zerada_para_none(linha["data_devolucao"]),
        "situacao": texto_ou_none(linha["situacao"]),
        "renovacao": texto_ou_none(linha["renovacao"]),
    }


def transformar_avaliacao_social(linha: dict) -> dict:
    """`casos_cancer_familia` **não** vira boolean — é `text` no legado,
    não `varchar(3)` como os outros campos Sim/Não desta tabela (ver
    `app/features/avaliacao_social/avaliacao_social.legacy.md`)."""
    return {
        "id": linha["id_avaliacao_social"],
        "id_pessoa": linha["id_pessoa"],
        "fumante": sim_nao_para_bool(linha["fumante"]),
        "residencia": texto_ou_none(linha["residencia"]),
        "energia_eletrica": sim_nao_para_bool(linha["energia_eletrica"]),
        "agua_encanada": sim_nao_para_bool(linha["agua_encanada"]),
        "tipo_construcao": texto_ou_none(linha["tipo_construcao"]),
        "renda_mensal_familiar": texto_ou_none(linha["renda_mensal_familiar"]),
        "quantas_pessoas_contribuem_formacao_renda": texto_ou_none(
            linha["quantas_pessoas_contribuem_formacao_renda"]
        ),
        "alguem_recebe_beneficio_previdenciario_governo": texto_ou_none(
            linha["alguem_recebe_beneficio_previdenciario_governo"]
        ),
        "diagnostico": texto_ou_none(linha["diagnostico"]),
        "tratamento_realizado": texto_ou_none(linha["tratamento_realizado"]),
        "casos_cancer_familia": texto_ou_none(linha["casos_cancer_familia"]),
        "necessita_medicamento_uso_continuo": sim_nao_para_bool(
            linha["necessita_medicamento_uso_continuo"]
        ),
        "medicamento_disponibilizado_sus": sim_nao_para_bool(
            linha["medicamento_disponibilizado_sus"]
        ),
        "custo_mensal_medicamento": texto_ou_none(linha["custo_mensal_medicamento"]),
        "alimentacao_especifica": texto_ou_none(linha["alimentacao_especifica"]),
        "equipamento_para_locomocao": texto_ou_none(linha["equipamento_para_locomocao"]),
        "data_movimento": datetime_zerado_para_none(linha["data_movimento"]),
    }


def transformar_composicao_familiar(linha: dict) -> dict:
    return {
        "id": linha["id_composicao_familiar"],
        "id_pessoa": linha["id_pessoa"],
        "nome": linha["nome"],
        "idade": texto_ou_none(linha["idade"]),
        "grau_parentesco": linha["grau_parentesco"],
        "estado_civil": texto_ou_none(linha["estado_civil"]),
        "renda": texto_ou_none(linha["renda"]),
        "ocupacao": texto_ou_none(linha["ocupacao"]),
    }
