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


def test_criar_emprestimo_com_itens_aninhados(client, db_session):
    deps = _criar_dependencias(db_session)

    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "itens": [
                {
                    "id_material": deps["material"].id,
                    "id_usuario": deps["usuario"].id,
                    "data_emprestimo": "2026-01-10",
                    "situacao": "Emprestado",
                }
            ],
        },
    )
    assert resposta.status_code == 201
    emprestimo_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens")
    assert resposta.status_code == 200
    itens = resposta.json()
    assert len(itens) == 1
    assert itens[0]["id_material"] == deps["material"].id
    assert itens[0]["situacao"] == "Emprestado"

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    tipos = {h["tipo"] for h in resposta.json()}
    assert tipos == {"Inclusão", "Item incluído"}


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
            "id_usuario": deps["usuario"].id,
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
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
        },
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "situacao": "Devolvido",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"
    assert resposta.json()["data_devolucao"] == "2026-02-10"
    assert resposta.json()["data_devolucao_efetiva"] == date.today().isoformat()


def test_data_devolucao_efetiva_e_limpa_se_situacao_deixa_de_ser_devolvido(client, db_session):
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
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "situacao": "Devolvido",
        },
    )
    item_id = resposta.json()["id"]
    assert resposta.json()["data_devolucao_efetiva"] == date.today().isoformat()

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "situacao": "Renovado",
        },
    )
    assert resposta.status_code == 200
    assert resposta.json()["data_devolucao_efetiva"] is None


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
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id},
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_2}/itens/{item_id}",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id},
    )

    assert resposta.status_code == 404


def test_buscar_emprestimo_inexistente(client):
    resposta = client.get("/api/emprestimos/999")

    assert resposta.status_code == 404


def test_itens_de_emprestimo_inexistente(client):
    resposta = client.get("/api/emprestimos/999/itens")

    assert resposta.status_code == 404


def test_historico_de_emprestimo_inexistente(client):
    resposta = client.get("/api/emprestimos/999/historico")

    assert resposta.status_code == 404


def test_criar_emprestimo_registra_historico_de_inclusao(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["tipo"] == "Inclusão"
    assert corpo[0]["id_usuario"] == deps["usuario"].id


def test_atualizar_observacao_por_acrescimo_registra_so_o_trecho_novo(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Primeira parte.",
        },
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Primeira parte. Segunda parte.",
        },
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    corpo = resposta.json()
    assert len(corpo) == 2
    alteracao = next(h for h in corpo if h["tipo"] == "Alteração")
    assert alteracao["observacao"] == "Segunda parte."


def test_atualizar_observacao_sem_prefixo_registra_de_para(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Texto original",
        },
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Texto totalmente diferente",
        },
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    alteracao = next(h for h in resposta.json() if h["tipo"] == "Alteração")
    assert 'de "Texto original" para "Texto totalmente diferente"' in alteracao["observacao"]


def test_atualizar_sem_mudar_observacao_nao_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Sempre igual",
        },
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Devolvido",
            "observacao": "Sempre igual",
        },
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["tipo"] == "Inclusão"


def test_adicionar_item_registra_historico(client, db_session):
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
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
            "situacao": "Emprestado",
        },
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    corpo = resposta.json()
    item_incluido = next(h for h in corpo if h["tipo"] == "Item incluído")
    assert "Cadeira de rodas" in item_incluido["observacao"]
    assert "situação: Emprestado" in item_incluido["observacao"]


def test_atualizar_item_registra_historico(client, db_session):
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
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
        },
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "situacao": "Devolvido",
        },
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    item_alterado = next(h for h in resposta.json() if h["tipo"] == "Item alterado")
    assert "situação: Devolvido" in item_alterado["observacao"]
