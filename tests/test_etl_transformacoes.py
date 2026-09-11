from datetime import date, datetime

from app.scripts.etl.transformacoes import (
    data_zerada_para_none,
    datetime_zerado_para_none,
    sim_nao_para_bool,
    texto_ou_none,
    transformar_avaliacao_social,
    transformar_estadia,
    transformar_hospital,
    transformar_material,
    transformar_pessoa,
    transformar_usuario,
)


def test_sim_nao_para_bool():
    assert sim_nao_para_bool("Sim") is True
    assert sim_nao_para_bool("Não") is False
    assert sim_nao_para_bool("não") is False
    assert sim_nao_para_bool(None) is None
    assert sim_nao_para_bool("") is None


def test_sim_nao_para_bool_com_espacos_nas_pontas():
    """Dado real tem valores como `'APMI '` — não é Sim/Não, mas em campos
    ativo/disponivel isso não deveria acontecer; o strip cobre o caso mais
    comum de 'Sim '/' Não'."""
    assert sim_nao_para_bool("Sim ") is True
    assert sim_nao_para_bool(" Não") is False


def test_data_zerada_para_none():
    assert data_zerada_para_none("0000-00-00") is None
    assert data_zerada_para_none(None) is None
    assert data_zerada_para_none("") is None
    assert data_zerada_para_none("2018-07-11") == date(2018, 7, 11)


def test_data_zerada_para_none_aceita_objeto_date():
    assert data_zerada_para_none(date(2018, 7, 11)) == date(2018, 7, 11)


def test_datetime_zerado_para_none():
    assert datetime_zerado_para_none("0000-00-00 00:00:00") is None
    assert datetime_zerado_para_none(None) is None
    assert datetime_zerado_para_none("2018-07-11 15:22:40") == datetime(2018, 7, 11, 15, 22, 40)


def test_texto_ou_none():
    assert texto_ou_none("") is None
    assert texto_ou_none(None) is None
    assert texto_ou_none("APMI ") == "APMI "


def test_transformar_hospital():
    linha = {"id_hospital": 1, "nome": "Hospital Regional", "ativo": "Sim"}

    resultado = transformar_hospital(linha)

    assert resultado == {"id": 1, "nome": "Hospital Regional", "ativo": True}


def test_transformar_pessoa_descarta_tipo():
    linha = {
        "id_pessoa": 1,
        "nome": "Maria",
        "data_nascimento": "1990-01-01",
        "rg": None,
        "cpf": "11111111111",
        "profissao": None,
        "cartao_sus": None,
        "endereco": None,
        "ponto_referencia": None,
        "telefone": None,
        "id_hospital": None,
        "id_municipio": None,
        "id_estado": None,
        "observacao": None,
        "tipo": "Paciente",
        "acompanhamento_social": None,
        "data_cadastro": "2018-07-11",
        "ativo": "Sim",
    }

    resultado = transformar_pessoa(linha)

    assert "tipo" not in resultado
    assert resultado["ativo"] is True
    assert resultado["data_nascimento"] == date(1990, 1, 1)


def test_transformar_usuario_mantem_senha_texto_plano():
    linha = {
        "id_usuario": 1,
        "login": "joana",
        "nome": "Joana",
        "perfil": "assistente_social",
        "ativo": "Sim",
        "senha": "123456",
    }

    resultado = transformar_usuario(linha)

    assert resultado["senha"] == "123456"
    assert resultado["senha_hash"] is None


def test_transformar_material_disponivel_emprestimo_nunca_none():
    linha = {
        "id_material": 1,
        "descricao": "Cadeira de rodas",
        "codigo_identificacao": None,
        "disponivel_emprestimo": None,
        "situacao": "Disponível",
        "local": "Casa",
        "observacao": None,
        "ativo": "Sim",
        "motivo_baixa": None,
    }

    resultado = transformar_material(linha)

    assert resultado["disponivel_emprestimo"] is False


def test_transformar_estadia_tipo_pessoa_default_paciente():
    linha = {
        "id_estadia": 1,
        "id_pessoa": 1,
        "id_quarto": 1,
        "id_usuario": 1,
        "data_entrada": "2018-07-11 00:00:00",
        "data_saida": None,
        "tempo_estadia": None,
        "tipo_pessoa": None,
        "situacao": "Finalizada",
        "observacao": None,
        "ativo": "Sim",
    }

    resultado = transformar_estadia(linha)

    assert resultado["tipo_pessoa"] == "Paciente"
    assert resultado["data_entrada"] == datetime(2018, 7, 11, 0, 0, 0)


def test_transformar_avaliacao_social_nao_converte_casos_cancer_familia():
    linha = {
        "id_avaliacao_social": 1,
        "id_pessoa": 1,
        "fumante": "Sim",
        "residencia": "Alugada",
        "energia_eletrica": "Sim",
        "agua_encanada": "Sim",
        "tipo_construcao": "Madeira",
        "renda_mensal_familiar": "1.300,00",
        "quantas_pessoas_contribuem_formacao_renda": "01",
        "alguem_recebe_beneficio_previdenciario_governo": "não",
        "diagnostico": None,
        "tratamento_realizado": None,
        "casos_cancer_familia": "Não",
        "necessita_medicamento_uso_continuo": "Não",
        "medicamento_disponibilizado_sus": "Sim",
        "custo_mensal_medicamento": None,
        "alimentacao_especifica": None,
        "equipamento_para_locomocao": None,
        "data_movimento": "2018-07-11 15:22:40",
    }

    resultado = transformar_avaliacao_social(linha)

    assert resultado["casos_cancer_familia"] == "Não"
    assert isinstance(resultado["casos_cancer_familia"], str)
    assert resultado["fumante"] is True
