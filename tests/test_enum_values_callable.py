"""Regressão do bug: sem `values_callable`, `Enum(..., native_enum=False)`
grava o *nome* do membro Python em vez do `.value` quando o INSERT/UPDATE
é feito pelo ORM (só fica certo via SQL cru, como a ETL do legado) — ver
migração 0018."""
from datetime import date, datetime

from sqlalchemy import text

from app.features.estadias.models import Estadia, SituacaoEstadia, TipoPessoaEstadia
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.solicitacoes_cadastro.models import (
    SituacaoSolicitacaoCadastro,
    SolicitacaoCadastroPaciente,
)
from app.features.usuarios.models import Usuario


def _valor_bruto_no_banco(db_session, tabela: str, coluna: str, id_coluna: str, id_valor: int) -> str:
    resultado = db_session.execute(
        text(f"SELECT {coluna} FROM {tabela} WHERE {id_coluna} = :id"), {"id": id_valor}
    ).scalar_one()
    return resultado


def test_estadia_situacao_e_tipo_pessoa_gravam_valor_nao_nome(db_session):
    pessoa = Pessoa(nome="Maria da Silva", data_nascimento=date(1990, 1, 1), data_cadastro=date.today())
    quarto = Quarto(numero="11", leito=4)
    usuario = Usuario(login="joana", nome="Joana", perfil="geral", senha="123456")
    db_session.add_all([pessoa, quarto, usuario])
    db_session.commit()

    estadia = Estadia(
        id_pessoa=pessoa.id,
        id_quarto=quarto.id,
        id_usuario=usuario.id,
        data_entrada=datetime(2026, 1, 10),
        situacao=SituacaoEstadia.EM_ACOMPANHAMENTO,
        tipo_pessoa=TipoPessoaEstadia.PACIENTE,
    )
    db_session.add(estadia)
    db_session.commit()
    db_session.refresh(estadia)

    assert (
        _valor_bruto_no_banco(db_session, "estadia", "situacao", "id_estadia", estadia.id)
        == "Em acompanhamento"
    )
    assert (
        _valor_bruto_no_banco(db_session, "estadia", "tipo_pessoa", "id_estadia", estadia.id)
        == "Paciente"
    )


def test_solicitacao_cadastro_situacao_grava_valor_nao_nome(db_session):
    solicitacao = SolicitacaoCadastroPaciente(
        nome="João Teste",
        data_nascimento=date(1990, 1, 1),
        situacao=SituacaoSolicitacaoCadastro.PENDENTE,
        data_solicitacao=datetime(2026, 1, 10),
    )
    db_session.add(solicitacao)
    db_session.commit()
    db_session.refresh(solicitacao)

    assert (
        _valor_bruto_no_banco(
            db_session, "solicitacao_cadastro_paciente", "situacao", "id", solicitacao.id
        )
        == "Pendente"
    )
