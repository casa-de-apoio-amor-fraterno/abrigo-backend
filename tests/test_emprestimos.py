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
                    "situacao": "Pendente",
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
    assert itens[0]["situacao"] == "Pendente"

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
            "situacao": "Pendente",
        },
    )
    assert resposta.status_code == 201
    item_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == item_id


def test_rejeita_situacao_invalida_no_item(client, db_session):
    # Combo fechado no legado (`rgpSituacao`, untFrmManutencaoEmprestimo.dfm)
    # com só 3 valores reais — qualquer outro texto deve ser rejeitado.
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
            "situacao": "Emprestado",
        },
    )
    assert resposta.status_code == 422


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
            "situacao": "Pendente",
        },
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico")
    corpo = resposta.json()
    item_incluido = next(h for h in corpo if h["tipo"] == "Item incluído")
    assert "Cadeira de rodas" in item_incluido["observacao"]
    assert "situação: Pendente" in item_incluido["observacao"]


def test_devolver_marca_emprestimo_itens_e_libera_material(client, db_session):
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
                    "situacao": "Pendente",
                }
            ],
        },
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id, "data_devolucao": "2026-02-15"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"

    itens = client.get(f"/api/emprestimos/{emprestimo_id}/itens").json()
    assert itens[0]["situacao"] == "Devolvido"
    assert itens[0]["data_devolucao_efetiva"] == "2026-02-15"

    material = client.get(f"/api/materiais/{deps['material'].id}").json()
    assert material["situacao"] == "Disponível"
    assert material["local"] == "Casa"
    assert material["disponivel_emprestimo"] is True

    historico = client.get(f"/api/emprestimos/{emprestimo_id}/historico").json()
    item_alterado = next(h for h in historico if h["tipo"] == "Item alterado")
    assert "situação: Devolvido" in item_alterado["observacao"]


def test_devolver_sem_data_usa_hoje(client, db_session):
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
                    "situacao": "Pendente",
                }
            ],
        },
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver", json={"id_usuario": deps["usuario"].id}
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"

    itens = client.get(f"/api/emprestimos/{emprestimo_id}/itens").json()
    assert itens[0]["data_devolucao_efetiva"] == date.today().isoformat()


def test_devolver_emprestimo_sem_itens_mantem_pendente(client, db_session):
    # `situacao` do cabeçalho é calculada a partir dos itens (achado
    # 2026-09-11, ver emprestimo.legacy.md) — sem nenhum item, o default é
    # sempre "Pendente" (mesma regra de `AtualizarSituacaoEmprestimo`),
    # mesmo chamando `/devolver` num empréstimo vazio.
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver", json={"id_usuario": deps["usuario"].id}
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Pendente"


def test_devolver_nao_reativa_material_ja_baixado(client, db_session):
    deps = _criar_dependencias(db_session)
    deps["material"].situacao = "Baixado"
    db_session.commit()

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
                    "situacao": "Pendente",
                }
            ],
        },
    )
    emprestimo_id = resposta.json()["id"]

    client.post(f"/api/emprestimos/{emprestimo_id}/devolver", json={"id_usuario": deps["usuario"].id})

    material = client.get(f"/api/materiais/{deps['material'].id}").json()
    assert material["situacao"] == "Baixado"


def test_devolver_ignora_itens_ja_devolvidos(client, db_session):
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
                    "situacao": "Devolvido",
                    "data_devolucao": "2026-01-01",
                }
            ],
        },
    )
    emprestimo_id = resposta.json()["id"]
    item_id = client.get(f"/api/emprestimos/{emprestimo_id}/itens").json()[0]["id"]
    data_efetiva_original = client.get(f"/api/emprestimos/{emprestimo_id}/itens").json()[0][
        "data_devolucao_efetiva"
    ]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id, "data_devolucao": "2026-03-01"},
    )

    item = client.get(f"/api/emprestimos/{emprestimo_id}/itens").json()[0]
    assert item["id"] == item_id
    assert item["data_devolucao_efetiva"] == data_efetiva_original

    historico = client.get(f"/api/emprestimos/{emprestimo_id}/historico").json()
    assert not any(h["tipo"] == "Item alterado" for h in historico)


def test_devolver_emprestimo_inexistente_retorna_404(client):
    resposta = client.post("/api/emprestimos/999/devolver", json={"id_usuario": 1})

    assert resposta.status_code == 404


def test_situacao_cabecalho_ignora_valor_enviado_pelo_cliente(client, db_session):
    # `Emprestimo.situacao` não é aceita como input (achado 2026-09-11, ver
    # emprestimo.legacy.md) — mandar o campo no corpo não tem efeito, o
    # valor é sempre calculado a partir dos itens.
    deps = _criar_dependencias(db_session)
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Devolvido"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["situacao"] == "Pendente"


def test_situacao_cabecalho_prioriza_renovado_sobre_pendente_e_devolvido(client, db_session):
    # Mesma prioridade de `AtualizarSituacaoEmprestimo`
    # (untFrmManutencaoEmprestimo.pas): qualquer item Renovado vence sobre
    # Pendente, que por sua vez vence sobre Devolvido.
    deps = _criar_dependencias(db_session)
    outro_material = Material(
        descricao="Muleta", situacao="Disponível", local="Casa", disponivel_emprestimo=True
    )
    db_session.add(outro_material)
    db_session.commit()
    db_session.refresh(outro_material)

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
                    "situacao": "Devolvido",
                }
            ],
        },
    )
    emprestimo_id = resposta.json()["id"]
    assert resposta.json()["situacao"] == "Devolvido"

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": outro_material.id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
        },
    )
    item_pendente_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}")
    assert resposta.json()["situacao"] == "Pendente"

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_pendente_id}",
        json={
            "id_material": outro_material.id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Renovado",
        },
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}")
    assert resposta.json()["situacao"] == "Renovado"


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
