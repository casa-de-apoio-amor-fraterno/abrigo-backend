from app.core.security import verificar_senha
from app.features.usuarios.models import Usuario
from app.scripts.hash_senhas_pendentes import hashear, listar_pendentes


def test_lista_apenas_usuarios_com_senha_em_texto_plano(db_session, usuario_legado, usuario_migrado):
    pendentes = listar_pendentes(db_session)

    assert [u.id for u in pendentes] == [usuario_legado.id]


def test_hashear_converte_senha_e_limpa_texto_plano(db_session, usuario_legado):
    hashear(db_session, [usuario_legado])

    usuario = db_session.get(Usuario, usuario_legado.id)
    assert usuario.senha is None
    assert usuario.senha_hash is not None
    assert verificar_senha("123456", usuario.senha_hash)


def test_apos_hashear_nao_sobra_pendente(db_session, usuario_legado):
    hashear(db_session, listar_pendentes(db_session))

    assert listar_pendentes(db_session) == []
