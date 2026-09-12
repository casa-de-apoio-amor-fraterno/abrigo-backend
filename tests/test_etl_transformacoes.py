from datetime import date, datetime

from app.scripts.etl.transformacoes import (
    data_zerada_para_none,
    datetime_zerado_para_none,
    parse_contatos,
    parse_tempo_estadia,
    sim_nao_para_bool,
    texto_ou_none,
    transformar_avaliacao_social,
    transformar_estadia,
    transformar_hospital,
    transformar_material,
    transformar_pessoa,
    transformar_quarto,
    transformar_usuario,
    transformar_voluntario,
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


def test_transformar_quarto_extrai_digitos_do_leito_sujo():
    # Dado real do dump: 'leito' varchar sujo — '2 leitos', '00003', '04'.
    linha_base = {"id_quarto": 1, "descricao": None, "numero": "11", "ativo": "Sim"}

    assert transformar_quarto({**linha_base, "leito": "2 leitos"})["leito"] == 2
    assert transformar_quarto({**linha_base, "leito": "00003"})["leito"] == 3
    assert transformar_quarto({**linha_base, "leito": "04"})["leito"] == 4
    assert transformar_quarto({**linha_base, "leito": "1"})["leito"] == 1


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
        "perfil": "Assistente Social",
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


def test_parse_tempo_estadia_vazio():
    assert parse_tempo_estadia(None) == (None, None)
    assert parse_tempo_estadia("") == (None, None)
    assert parse_tempo_estadia("   ") == (None, None)


def test_parse_tempo_estadia_dias_singular_e_plural():
    assert parse_tempo_estadia("1 dia") == (1, "dias")
    assert parse_tempo_estadia("4 dias") == (4, "dias")


def test_parse_tempo_estadia_zero_a_esquerda_e_espacos():
    """Dado real: '06 dias '."""
    assert parse_tempo_estadia("06 dias ") == (6, "dias")


def test_parse_tempo_estadia_case_insensitive():
    assert parse_tempo_estadia("1 DIA") == (1, "dias")
    assert parse_tempo_estadia("2 Dias") == (2, "dias")


def test_parse_tempo_estadia_noites_e_horas():
    assert parse_tempo_estadia("1 noite") == (1, "noites")
    assert parse_tempo_estadia("2 noites") == (2, "noites")
    assert parse_tempo_estadia("3 horas") == (3, "horas")


def test_parse_tempo_estadia_numero_sozinho_vira_dias():
    """Dado real: valores como '1', '2' sem unidade escrita — decisão do
    time: tratar como dias, unidade predominante no restante dos dados."""
    assert parse_tempo_estadia("1") == (1, "dias")
    assert parse_tempo_estadia("15") == (15, "dias")


def test_parse_tempo_estadia_texto_nao_reconhecido_nao_migra():
    """Dado real usado como observação, não duração — não deve virar um
    valor inventado; o texto original continua em `tempo_estadia`."""
    assert parse_tempo_estadia("não pernoitou") == (None, None)
    assert parse_tempo_estadia("TROCA DE QUARTO") == (None, None)
    assert parse_tempo_estadia("2 hrs 30minutos") == (None, None)
    assert parse_tempo_estadia("dois dias") == (None, None)


def test_parse_contatos_vazio():
    assert parse_contatos(None) == []
    assert parse_contatos("") == []
    assert parse_contatos("   ") == []


def test_parse_contatos_numero_unico():
    resultado = parse_contatos("988132030")

    assert resultado == [
        {"numero": "988132030", "nome_contato": None, "observacao": None, "principal": True}
    ]


def test_parse_contatos_multiplos_numeros_separados_por_barra():
    """Dado real: '(42)9857-1037/(42)99989-5775'."""
    resultado = parse_contatos("(42)9857-1037/(42)99989-5775")

    assert [c["numero"] for c in resultado] == ["(42)9857-1037", "(42)99989-5775"]
    assert resultado[0]["principal"] is True
    assert resultado[1]["principal"] is False


def test_parse_contatos_multiplos_numeros_separados_por_espacos():
    """Dado real: '47-3642-6822      47-98411-2834        47-999969197'."""
    resultado = parse_contatos("47-3642-6822      47-98411-2834        47-999969197")

    assert [c["numero"] for c in resultado] == ["47-3642-6822", "47-98411-2834", "47-999969197"]


def test_parse_contatos_separa_nome_de_quem_atende():
    """Dado real: '42-98818-3580 Sidney        98827-3809 esposa'."""
    resultado = parse_contatos("42-98818-3580 Sidney        98827-3809 esposa")

    assert resultado[0]["numero"] == "42-98818-3580"
    assert resultado[0]["nome_contato"] == "Sidney"
    assert resultado[1]["numero"] == "98827-3809"
    assert resultado[1]["nome_contato"] == "esposa"


def test_parse_contatos_separador_ou():
    """Dado real: '3522 5571 ou 88450659'."""
    resultado = parse_contatos("3522 5571 ou 88450659")

    assert [c["numero"] for c in resultado] == ["3522 5571", "88450659"]


def test_parse_contatos_texto_nao_reconhecido_nao_perde_dado():
    """Segmento sem número reconhecível preserva o texto original inteiro
    e sinaliza revisão manual — nunca é descartado silenciosamente."""
    resultado = parse_contatos("Sem telefone")

    assert len(resultado) == 1
    assert resultado[0]["numero"] == "Sem telefone"
    assert resultado[0]["observacao"] is not None


def test_transformar_pessoa_nao_inclui_telefone():
    """`telefone` foi removido do schema de `Pessoa` — normalizado em
    `PessoaContato` via `parse_contatos`, não copiado direto."""
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
        "telefone": "999999999",
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

    assert "telefone" not in resultado


def test_transformar_voluntario_nao_inclui_telefone():
    linha = {
        "id_voluntario": 1,
        "nome": "João",
        "telefone": "999999999",
        "setor": None,
        "data_nascimento": None,
        "estado_civil": None,
        "cpf": None,
        "endereco": None,
        "formacao": None,
        "observacao": None,
        "ativo": "Sim",
    }

    resultado = transformar_voluntario(linha)

    assert "telefone" not in resultado


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
