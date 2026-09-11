from datetime import date

from app.features.emprestimos.models import Emprestimo
from app.features.materiais.models import Material
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario


def _criar_dependencias(db_session) -> dict:
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    material = Material(descricao="Cadeira de rodas", situacao="Disponível", local="Casa", disponivel_emprestimo=True)
    db_session.add_all([pessoa, usuario, material])
    db_session.commit()
    db_session.refresh(pessoa)
    db_session.refresh(usuario)
    db_session.refresh(material)
    return {"pessoa": pessoa, "usuario": usuario, "material": material}


def test_listar_vazio(client):
    resposta = client.get("/api/emprestimos")

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_criar_e_buscar_emprestimo(client, db_session):
    deps = _criar_dependencias(db_session)

    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    assert resposta.status_code == 201
    emprestimo_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}")
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Pendente"
    assert resposta.json()["ativo"] is True


def test_listar_filtrado_por_situacao(client, db_session):
    deps = _criar_dependencias(db_session)
    db_session.add_all(
        [
            Emprestimo(id_pessoa=deps["pessoa"].id, id_usuario=deps["usuario"].id, situacao="Pendente"),
            Emprestimo(id_pessoa=deps["pessoa"].id, id_usuario=deps["usuario"].id, situacao="Devolvido"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/emprestimos", params={"situacao": "Devolvido"})

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["situacao"] == "Devolvido"


def test_inativar_emprestimo(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.delete(f"/api/emprestimos/{emprestimo_id}")
    assert resposta.status_code == 204

    resposta = client.get("/api/emprestimos")
    assert resposta.json()["total"] == 0


def test_adicionar_e_listar_item(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "data_emprestimo": "2026-01-10",
            "situacao": "Emprestado",
        },
    )
    assert resposta.status_code == 201
    item_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == item_id


def test_atualizar_item_marcando_devolucao(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_id = resposta.json()["id"]
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "data_emprestimo": "2026-01-10"},
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "situacao": "Devolvido",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"
    assert resposta.json()["data_devolucao"] == "2026-02-10"


def test_item_de_outro_emprestimo_retorna_404(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_1 = resposta.json()["id"]
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_2 = resposta.json()["id"]
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_1}/itens",
        json={"id_material": deps["material"].id},
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_2}/itens/{item_id}",
        json={"id_material": deps["material"].id},
    )

    assert resposta.status_code == 404


def test_buscar_emprestimo_inexistente(client):
    resposta = client.get("/api/emprestimos/999")

    assert resposta.status_code == 404


def test_itens_de_emprestimo_inexistente(client):
    resposta = client.get("/api/emprestimos/999/itens")

    assert resposta.status_code == 404
