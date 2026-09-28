from datetime import date

from app.core.security import criar_token_acesso
from app.features.emprestimos.models import Emprestimo
from app.features.materiais.models import Material
from app.features.materiais_locais.models import MaterialLocal
from app.features.pessoas.models import Pessoa
from app.features.usuarios.models import Usuario


def _auth_header(usuario) -> dict:
    token = criar_token_acesso(usuario.id)
    return {"Authorization": f"Bearer {token}"}


def _criar_dependencias(db_session) -> dict:
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    local_casa = MaterialLocal(nome="Casa")
    db_session.add_all([pessoa, usuario, local_casa])
    db_session.commit()
    material = Material(
        descricao="Cadeira de rodas", situacao="Disponível", id_local=local_casa.id, disponivel_emprestimo=True
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(pessoa)
    db_session.refresh(usuario)
    db_session.refresh(material)
    return {"pessoa": pessoa, "usuario": usuario, "material": material, "local_casa": local_casa}


def test_listar_exige_login(client):
    resposta = client.get("/api/emprestimos")

    assert resposta.status_code == 401


def test_listar_vazio(client, usuario_legado):
    resposta = client.get("/api/emprestimos", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 200
    assert resposta.json() == {"items": [], "total": 0}


def test_criar_e_buscar_emprestimo(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    assert resposta.status_code == 201
    emprestimo_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Pendente"
    assert resposta.json()["ativo"] is True


def test_criar_emprestimo_com_itens_aninhados(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_emprestimo": "2026-01-10",
            "itens": [
                {
                    "id_material": deps["material"].id,
                    "id_usuario": deps["usuario"].id,
                    "situacao": "Pendente",
                }
            ],
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    emprestimo_id = resposta.json()["id"]
    assert resposta.json()["data_emprestimo"] == "2026-01-10"

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers)
    assert resposta.status_code == 200
    itens = resposta.json()
    assert len(itens) == 1
    assert itens[0]["id_material"] == deps["material"].id
    assert itens[0]["situacao"] == "Pendente"

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    tipos = {h["tipo"] for h in resposta.json()}
    assert tipos == {"Inclusão", "Item incluído"}


def test_listar_filtrado_por_situacao(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    db_session.add_all(
        [
            Emprestimo(id_pessoa=deps["pessoa"].id, id_usuario=deps["usuario"].id, situacao="Pendente"),
            Emprestimo(id_pessoa=deps["pessoa"].id, id_usuario=deps["usuario"].id, situacao="Devolvido"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/emprestimos", params={"situacao": "Devolvido"}, headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["situacao"] == "Devolvido"


def test_listar_filtrado_por_busca_nome_pessoa(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    outra_pessoa = Pessoa(nome="João Pereira", data_nascimento=date(1985, 3, 3), data_cadastro=date.today())
    db_session.add(outra_pessoa)
    db_session.commit()
    db_session.refresh(outra_pessoa)

    db_session.add_all(
        [
            Emprestimo(id_pessoa=deps["pessoa"].id, id_usuario=deps["usuario"].id, situacao="Pendente"),
            Emprestimo(id_pessoa=outra_pessoa.id, id_usuario=deps["usuario"].id, situacao="Pendente"),
        ]
    )
    db_session.commit()

    resposta = client.get("/api/emprestimos", params={"busca": "maria"}, headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["id_pessoa"] == deps["pessoa"].id


def test_inativar_emprestimo(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.delete(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.status_code == 204

    resposta = client.get("/api/emprestimos", headers=headers)
    assert resposta.json()["total"] == 0


def test_adicionar_e_listar_item(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
        },
        headers=headers,
    )
    assert resposta.status_code == 201
    item_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id"] == item_id


def test_rejeita_material_duplicado_no_mesmo_emprestimo(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )

    assert resposta.status_code == 409
    assert "já está incluído" in resposta.json()["detail"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers)
    assert len(resposta.json()) == 1


def test_rejeita_material_duplicado_na_criacao_com_itens_aninhados(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "itens": [
                {"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
                {"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
            ],
        },
        headers=headers,
    )

    assert resposta.status_code == 409
    assert "já está incluído" in resposta.json()["detail"]


def test_permite_reincluir_material_ja_devolvido_no_mesmo_emprestimo(client, db_session):
    # Um item "Devolvido" não bloqueia reincluir o mesmo material — o
    # empréstimo anterior daquele item já terminou.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Devolvido"},
        headers=headers,
    )
    assert resposta.status_code == 201

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    assert resposta.status_code == 201


def test_rejeita_material_duplicado_ao_atualizar_item(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    outro_material = Material(
        descricao="Muleta", situacao="Disponível", id_local=deps["local_casa"].id, disponivel_emprestimo=True
    )
    db_session.add(outro_material)
    db_session.commit()
    db_session.refresh(outro_material)

    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": outro_material.id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    item_id = resposta.json()["id"]

    # Tenta editar o item da muleta pra apontar pro material já usado pelo outro item.
    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )

    assert resposta.status_code == 409


def test_rejeita_situacao_invalida_no_item(client, db_session):
    # Combo fechado no legado (`rgpSituacao`, untFrmManutencaoEmprestimo.dfm)
    # com só 3 valores reais — qualquer outro texto deve ser rejeitado.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Emprestado",
        },
        headers=headers,
    )
    assert resposta.status_code == 422


def test_atualizar_item_marcando_devolucao(client, db_session):
    # Prazo (data_emprestimo/data_devolucao) e data_devolucao_efetiva moraram
    # pro nível do empréstimo (não mais do item, ver models.py) — decisão do
    # time (2026-09-28): com itens de prazos distintos no mesmo empréstimo, o
    # contrato de renovação não batia corretamente.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id},
        headers=headers,
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Devolvido",
        },
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.json()["data_devolucao"] == "2026-02-10"
    assert resposta.json()["data_devolucao_efetiva"] == date.today().isoformat()


def test_data_devolucao_efetiva_e_limpa_se_situacao_deixa_de_ser_devolvido(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "itens": [
                {
                    "id_material": deps["material"].id,
                    "id_usuario": deps["usuario"].id,
                    "situacao": "Devolvido",
                }
            ],
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]
    assert resposta.json()["data_devolucao_efetiva"] == date.today().isoformat()
    item_id = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()[0]["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_id}",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Renovado",
        },
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.json()["data_devolucao_efetiva"] is None


def test_item_de_outro_emprestimo_retorna_404(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_1 = resposta.json()["id"]
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_2 = resposta.json()["id"]
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_1}/itens",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id},
        headers=headers,
    )
    item_id = resposta.json()["id"]

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_2}/itens/{item_id}",
        json={"id_material": deps["material"].id, "id_usuario": deps["usuario"].id},
        headers=headers,
    )

    assert resposta.status_code == 404


def test_buscar_emprestimo_inexistente(client, usuario_legado):
    resposta = client.get("/api/emprestimos/999", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_itens_de_emprestimo_inexistente(client, usuario_legado):
    resposta = client.get("/api/emprestimos/999/itens", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_historico_de_emprestimo_inexistente(client, usuario_legado):
    resposta = client.get("/api/emprestimos/999/historico", headers=_auth_header(usuario_legado))

    assert resposta.status_code == 404


def test_criar_emprestimo_registra_historico_de_inclusao(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["tipo"] == "Inclusão"
    assert corpo[0]["id_usuario"] == deps["usuario"].id


def test_atualizar_observacao_por_acrescimo_registra_so_o_trecho_novo(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Primeira parte.",
        },
        headers=headers,
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
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    corpo = resposta.json()
    assert len(corpo) == 2
    alteracao = next(h for h in corpo if h["tipo"] == "Alteração")
    assert alteracao["observacao"] == "Segunda parte."


def test_atualizar_observacao_sem_prefixo_registra_de_para(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Texto original",
        },
        headers=headers,
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
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    alteracao = next(h for h in resposta.json() if h["tipo"] == "Alteração")
    assert 'de "Texto original" para "Texto totalmente diferente"' in alteracao["observacao"]


def test_atualizar_sem_mudar_observacao_nao_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "observacao": "Sempre igual",
        },
        headers=headers,
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
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["tipo"] == "Inclusão"


def test_adicionar_item_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
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
        headers=headers,
    )
    assert resposta.status_code == 201

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    corpo = resposta.json()
    item_incluido = next(h for h in corpo if h["tipo"] == "Item incluído")
    assert "Cadeira de rodas" in item_incluido["observacao"]
    assert "situação: Pendente" in item_incluido["observacao"]


def test_devolver_marca_emprestimo_itens_e_libera_material(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_emprestimo": "2026-01-10",
            "itens": [
                {
                    "id_material": deps["material"].id,
                    "id_usuario": deps["usuario"].id,
                    "situacao": "Pendente",
                }
            ],
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id, "data_devolucao": "2026-02-15"},
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"
    assert resposta.json()["data_devolucao_efetiva"] == "2026-02-15"

    itens = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()
    assert itens[0]["situacao"] == "Devolvido"

    material = client.get(f"/api/materiais/{deps['material'].id}", headers=headers).json()
    assert material["situacao"] == "Disponível"
    assert material["id_local"] == deps["local_casa"].id
    assert material["disponivel_emprestimo"] is True

    historico = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers).json()
    item_alterado = next(h for h in historico if h["tipo"] == "Item alterado")
    assert "situação: Devolvido" in item_alterado["observacao"]


def test_devolver_sem_data_usa_hoje(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id},
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"
    assert resposta.json()["data_devolucao_efetiva"] == date.today().isoformat()


def test_devolver_emprestimo_sem_itens_mantem_pendente(client, db_session):
    # `situacao` do cabeçalho é calculada a partir dos itens (achado
    # 2026-09-11, ver emprestimo.legacy.md) — sem nenhum item, o default é
    # sempre "Pendente" (mesma regra de `AtualizarSituacaoEmprestimo`),
    # mesmo chamando `/devolver` num empréstimo vazio.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id},
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Pendente"


def test_devolver_nao_reativa_material_ja_inutilizado(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    deps["material"].situacao = "Inutilizado"
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
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id},
        headers=headers,
    )

    material = client.get(f"/api/materiais/{deps['material'].id}", headers=headers).json()
    assert material["situacao"] == "Inutilizado"


def test_devolver_ignora_itens_ja_devolvidos(client, db_session):
    # Empréstimo já totalmente devolvido: chamar /devolver de novo não deve
    # mexer em nada (idempotente) — nem tocar em `data_devolucao_efetiva`
    # já gravada, nem gerar novo histórico de item.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
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
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]
    data_efetiva_original = resposta.json()["data_devolucao_efetiva"]
    item_id = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()[0]["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/devolver",
        json={"id_usuario": deps["usuario"].id, "data_devolucao": "2026-03-01"},
        headers=headers,
    )

    assert resposta.json()["data_devolucao_efetiva"] == data_efetiva_original

    item = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()[0]
    assert item["id"] == item_id

    historico = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers).json()
    assert not any(h["tipo"] == "Item alterado" for h in historico)


def test_devolver_emprestimo_inexistente_retorna_404(client, usuario_legado):
    resposta = client.post(
        "/api/emprestimos/999/devolver",
        json={"id_usuario": 1},
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 404


def test_renovar_soma_dias_a_partir_da_data_devolucao_atual(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_emprestimo": "2026-01-10",
            "data_devolucao": "2026-02-10",
            "itens": [
                {"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"}
            ],
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/renovar",
        json={"id_usuario": deps["usuario"].id, "dias": 20},
        headers=headers,
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["data_devolucao"] == "2026-03-02"
    assert corpo["situacao"] == "Renovado"

    itens = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()
    assert itens[0]["situacao"] == "Renovado"

    historico = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers).json()
    assert any(h["tipo"] == "Renovação" for h in historico)


def test_renovar_sem_data_devolucao_usa_hoje_como_base(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/renovar",
        json={"id_usuario": deps["usuario"].id, "dias": 5},
        headers=headers,
    )

    assert resposta.status_code == 200
    from datetime import timedelta

    assert resposta.json()["data_devolucao"] == (date.today() + timedelta(days=5)).isoformat()


def test_renovar_nao_reabre_item_ja_devolvido(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "itens": [
                {"id_material": deps["material"].id, "id_usuario": deps["usuario"].id, "situacao": "Devolvido"}
            ],
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/renovar",
        json={"id_usuario": deps["usuario"].id, "dias": 10},
        headers=headers,
    )

    assert resposta.status_code == 200
    assert resposta.json()["situacao"] == "Devolvido"

    itens = client.get(f"/api/emprestimos/{emprestimo_id}/itens", headers=headers).json()
    assert itens[0]["situacao"] == "Devolvido"


def test_renovar_dias_invalido_retorna_422(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/renovar",
        json={"id_usuario": deps["usuario"].id, "dias": 0},
        headers=headers,
    )

    assert resposta.status_code == 422


def test_renovar_emprestimo_inexistente_retorna_404(client, usuario_legado):
    resposta = client.post(
        "/api/emprestimos/999/renovar",
        json={"id_usuario": 1, "dias": 10},
        headers=_auth_header(usuario_legado),
    )

    assert resposta.status_code == 404


def test_situacao_cabecalho_ignora_valor_enviado_pelo_cliente(client, db_session):
    # `Emprestimo.situacao` não é aceita como input (achado 2026-09-11, ver
    # emprestimo.legacy.md) — mandar o campo no corpo não tem efeito, o
    # valor é sempre calculado a partir dos itens.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Devolvido"},
        headers=headers,
    )
    assert resposta.status_code == 201
    assert resposta.json()["situacao"] == "Pendente"


def test_situacao_cabecalho_prioriza_renovado_sobre_pendente_e_devolvido(client, db_session):
    # Mesma prioridade de `AtualizarSituacaoEmprestimo`
    # (untFrmManutencaoEmprestimo.pas): qualquer item Renovado vence sobre
    # Pendente, que por sua vez vence sobre Devolvido.
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    outro_material = Material(
        descricao="Muleta", situacao="Disponível", id_local=deps["local_casa"].id, disponivel_emprestimo=True
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
        headers=headers,
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
        headers=headers,
    )
    item_pendente_id = resposta.json()["id"]

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.json()["situacao"] == "Pendente"

    resposta = client.put(
        f"/api/emprestimos/{emprestimo_id}/itens/{item_pendente_id}",
        json={
            "id_material": outro_material.id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Renovado",
        },
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}", headers=headers)
    assert resposta.json()["situacao"] == "Renovado"


def test_atualizar_item_registra_historico(client, db_session):
    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])
    resposta = client.post(
        "/api/emprestimos",
        json={"id_pessoa": deps["pessoa"].id, "id_usuario": deps["usuario"].id, "situacao": "Pendente"},
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]
    resposta = client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "data_emprestimo": "2026-01-10",
        },
        headers=headers,
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
        headers=headers,
    )
    assert resposta.status_code == 200

    resposta = client.get(f"/api/emprestimos/{emprestimo_id}/historico", headers=headers)
    item_alterado = next(h for h in resposta.json() if h["tipo"] == "Item alterado")
    assert "situação: Devolvido" in item_alterado["observacao"]


def test_alertas_vencimento_exige_login(client):
    resposta = client.get("/api/emprestimos/alertas-vencimento")

    assert resposta.status_code == 401


def test_alertas_vencimento_lista_itens_dentro_do_horizonte(client, db_session):
    from datetime import timedelta

    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    vence_em_5_dias = (date.today() + timedelta(days=5)).isoformat()
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_devolucao": vence_em_5_dias,
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
        },
        headers=headers,
    )

    resposta = client.get("/api/emprestimos/alertas-vencimento", headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["id_emprestimo"] == emprestimo_id
    assert corpo[0]["nome_pessoa"] == deps["pessoa"].nome
    assert corpo[0]["descricao_material"] == deps["material"].descricao
    assert corpo[0]["dias_restantes"] == 5


def test_alertas_vencimento_inclui_vencidos_com_dias_negativos(client, db_session):
    from datetime import timedelta

    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    venceu_ha_3_dias = (date.today() - timedelta(days=3)).isoformat()
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_devolucao": venceu_ha_3_dias,
        },
        headers=headers,
    )
    emprestimo_id = resposta.json()["id"]

    client.post(
        f"/api/emprestimos/{emprestimo_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
        },
        headers=headers,
    )

    resposta = client.get("/api/emprestimos/alertas-vencimento", headers=headers)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["dias_restantes"] == -3


def test_alertas_vencimento_ignora_itens_devolvidos_e_fora_do_horizonte(client, db_session):
    # `data_devolucao` é do empréstimo (compartilhada por todos os itens,
    # ver models.py) — dois empréstimos separados pra isolar os dois
    # motivos de exclusão: um fora do horizonte, outro com o único item já
    # devolvido.
    from datetime import timedelta

    deps = _criar_dependencias(db_session)
    headers = _auth_header(deps["usuario"])

    longe = (date.today() + timedelta(days=30)).isoformat()
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_devolucao": longe,
        },
        headers=headers,
    )
    emprestimo_longe_id = resposta.json()["id"]
    client.post(
        f"/api/emprestimos/{emprestimo_longe_id}/itens",
        json={
            "id_material": deps["material"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
        },
        headers=headers,
    )

    outro_material = Material(
        descricao="Muleta",
        situacao="Disponível",
        id_local=deps["local_casa"].id,
        disponivel_emprestimo=True,
    )
    db_session.add(outro_material)
    db_session.commit()
    db_session.refresh(outro_material)

    perto = (date.today() + timedelta(days=2)).isoformat()
    resposta = client.post(
        "/api/emprestimos",
        json={
            "id_pessoa": deps["pessoa"].id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Pendente",
            "data_devolucao": perto,
        },
        headers=headers,
    )
    emprestimo_perto_id = resposta.json()["id"]
    client.post(
        f"/api/emprestimos/{emprestimo_perto_id}/itens",
        json={
            "id_material": outro_material.id,
            "id_usuario": deps["usuario"].id,
            "situacao": "Devolvido",
        },
        headers=headers,
    )

    resposta = client.get("/api/emprestimos/alertas-vencimento", headers=headers)

    assert resposta.status_code == 200
    assert resposta.json() == []
