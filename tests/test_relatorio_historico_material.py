from datetime import date

from app.core.security import criar_token_acesso
from app.features.emprestimos.models import Emprestimo, EmprestimoItem
from app.features.materiais.models import Material
from app.features.materiais_locais.models import MaterialLocal
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario


def _auth_header(usuario) -> dict:
    return {"Authorization": f"Bearer {criar_token_acesso(usuario.id)}"}


def _preparar(db_session) -> dict:
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    local = MaterialLocal(nome="Casa")
    maria = Pessoa(nome="Maria", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    jose = Pessoa(nome="José", data_nascimento=date(1980, 1, 1), data_cadastro=date.today())
    db_session.add_all([usuario, local, maria, jose])
    db_session.commit()
    material = Material(
        descricao="Cadeira de rodas",
        numero_patrimonio="10945",
        situacao="Disponível",
        id_local=local.id,
        disponivel_emprestimo=True,
    )
    db_session.add(material)
    db_session.commit()
    for pessoa, inicio in ((maria, date(2025, 1, 10)), (jose, date(2025, 6, 1))):
        emprestimo = Emprestimo(
            id_pessoa=pessoa.id,
            id_usuario=usuario.id,
            situacao="Devolvido",
            data_emprestimo=inicio,
            data_devolucao=inicio.replace(month=inicio.month + 1),
            ativo=True,
        )
        db_session.add(emprestimo)
        db_session.commit()
        db_session.add(EmprestimoItem(id_emprestimo=emprestimo.id, id_material=material.id, situacao="Devolvido"))
        db_session.commit()
    return {"usuario": usuario, "material": material}


def test_resumo_historico_material(client, db_session):
    deps = _preparar(db_session)

    resposta = client.get(
        f"/api/relatorios/historico-material/resumo?id_material={deps['material'].id}",
        headers=_auth_header(deps["usuario"]),
    )

    assert resposta.status_code == 200
    valores = {i["rotulo"]: i["valor"] for i in resposta.json()["itens"]}
    assert valores["Empréstimos do item"] == "2"
    assert valores["Pessoas atendidas"] == "2"
    assert valores["Último empréstimo"] == "01/06/2025"


def test_pdf_historico_material(client, db_session):
    deps = _preparar(db_session)

    resposta = client.get(
        f"/api/relatorios/historico-material/pdf?id_material={deps['material'].id}",
        headers=_auth_header(deps["usuario"]),
    )

    assert resposta.status_code == 200
    assert resposta.content.startswith(b"%PDF")


def test_historico_material_inexistente_retorna_404(client, db_session):
    deps = _preparar(db_session)

    resposta = client.get(
        "/api/relatorios/historico-material/pdf?id_material=99999", headers=_auth_header(deps["usuario"])
    )

    assert resposta.status_code == 404
