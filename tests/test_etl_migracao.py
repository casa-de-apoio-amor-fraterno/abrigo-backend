from app.features.estados.models import Estado
from app.scripts.etl_migracao import _resincronizar_sequencia


def test_resincronizar_sequencia_ignora_bancos_nao_postgres(db_session):
    """SQLite (usado nos testes) não tem `setval`/sequences do Postgres —
    a função deve simplesmente não fazer nada, sem levantar erro."""
    _resincronizar_sequencia(db_session, Estado)
