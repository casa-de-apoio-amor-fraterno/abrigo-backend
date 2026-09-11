from app.scripts.etl.reconciliacao import RegistroAcompanhamento, reconciliar


def test_reconcilia_quando_paciente_tem_uma_unica_estadia():
    registros = [RegistroAcompanhamento(id_acompanhamento=1, id_paciente=9, id_acompanhante=10)]
    estadias_por_pessoa = {9: [100]}

    resultado = reconciliar(registros, estadias_por_pessoa)

    assert resultado.reconciliados == [{"id_estadia": 100, "id_pessoa": 10}]
    assert resultado.pendentes_revisao_manual == []


def test_pendente_quando_paciente_tem_multiplas_estadias():
    registros = [RegistroAcompanhamento(id_acompanhamento=1, id_paciente=9, id_acompanhante=10)]
    estadias_por_pessoa = {9: [100, 101]}

    resultado = reconciliar(registros, estadias_por_pessoa)

    assert resultado.reconciliados == []
    assert resultado.pendentes_revisao_manual == registros


def test_pendente_quando_paciente_nao_tem_estadia():
    registros = [RegistroAcompanhamento(id_acompanhamento=1, id_paciente=9, id_acompanhante=10)]

    resultado = reconciliar(registros, estadias_por_pessoa={})

    assert resultado.reconciliados == []
    assert resultado.pendentes_revisao_manual == registros


def test_reconcilia_varios_registros_independentemente():
    registros = [
        RegistroAcompanhamento(id_acompanhamento=1, id_paciente=9, id_acompanhante=10),
        RegistroAcompanhamento(id_acompanhamento=2, id_paciente=11, id_acompanhante=12),
        RegistroAcompanhamento(id_acompanhamento=3, id_paciente=9, id_acompanhante=13),
    ]
    estadias_por_pessoa = {9: [100], 11: [200, 201]}

    resultado = reconciliar(registros, estadias_por_pessoa)

    assert len(resultado.reconciliados) == 2
    assert {"id_estadia": 100, "id_pessoa": 10} in resultado.reconciliados
    assert {"id_estadia": 100, "id_pessoa": 13} in resultado.reconciliados
    assert len(resultado.pendentes_revisao_manual) == 1
    assert resultado.pendentes_revisao_manual[0].id_paciente == 11
