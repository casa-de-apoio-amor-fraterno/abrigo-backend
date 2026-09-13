import pytest

from app.features.estados.models import Estado
from app.scripts.etl_migracao import _resincronizar_sequencia, _validar_identificador


def test_resincronizar_sequencia_ignora_bancos_nao_postgres(db_session):
    """SQLite (usado nos testes) não tem `setval`/sequences do Postgres —
    a função deve simplesmente não fazer nada, sem levantar erro."""
    _resincronizar_sequencia(db_session, Estado)


def test_validar_identificador_aceita_nomes_de_tabela_conhecidos():
    for nome in ("pessoa", "estadia_acompanhante", "id_pessoa"):
        assert _validar_identificador(nome) == nome


@pytest.mark.parametrize(
    "identificador_malicioso",
    ["pessoa; DROP TABLE usuario;--", "pessoa`; DROP TABLE usuario;--", "", "1pessoa"],
)
def test_validar_identificador_recusa_entrada_maliciosa(identificador_malicioso):
    with pytest.raises(ValueError):
        _validar_identificador(identificador_malicioso)
