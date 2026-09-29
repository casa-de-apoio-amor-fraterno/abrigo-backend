from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.estadias.models import Estadia, EstadiaAcompanhante, SituacaoEstadia, TipoPessoaEstadia
from app.features.pessoas.models import Pessoa
from app.features.quartos.models import Quarto
from app.features.quartos.schemas import QuartoCreate, QuartoUpdate


def listar(db: Session, apenas_ativos: bool = True) -> list[Quarto]:
    consulta = select(Quarto).order_by(Quarto.numero)
    if apenas_ativos:
        consulta = consulta.where(Quarto.ativo.is_(True))
    return list(db.scalars(consulta).all())


def listar_ocupacao(db: Session) -> list[dict]:
    # "Situação != Finalizada" sozinho não é confiável (achado 2026-09-12,
    # ver QuartoOcupacaoResponse) — estadias 'Em acompanhamento' nunca
    # fechadas no legado inflam a contagem (ex.: quarto de 4 leitos com 39
    # estadias "ativas", algumas de 2018). Só as `leito` mais recentes por
    # quarto contam como ocupantes de verdade; o resto vira
    # `pendentes_revisao`, pra equipe finalizar manualmente.
    quartos = listar(db, apenas_ativos=True)

    linhas = db.execute(
        select(
            Estadia.id,
            Estadia.id_quarto,
            Estadia.id_pessoa,
            Estadia.data_entrada,
            Pessoa.nome,
            Estadia.tipo_pessoa,
        )
        .join(Pessoa, Pessoa.id == Estadia.id_pessoa)
        .where(Estadia.situacao == SituacaoEstadia.EM_ACOMPANHAMENTO)
        .order_by(Estadia.id_quarto, Estadia.data_entrada.desc())
    ).all()

    por_quarto: dict[int, list[dict]] = {}
    for id_estadia, id_quarto, id_pessoa, data_entrada, nome_pessoa, tipo_pessoa in linhas:
        por_quarto.setdefault(id_quarto, []).append(
            {
                "id_estadia": id_estadia,
                "id_pessoa": id_pessoa,
                "nome_pessoa": nome_pessoa,
                "data_entrada": data_entrada,
                # Titular da estadia com leito próprio já cadastrado como
                # Acompanhante (tipo_pessoa) — colorido igual ao
                # EstadiaAcompanhante.ocupa_leito abaixo, embora sejam
                # conceitos diferentes (ver Estadia.tipo_pessoa vs
                # EstadiaAcompanhante, em models.py).
                "acompanhante": tipo_pessoa == TipoPessoaEstadia.ACOMPANHANTE,
            }
        )

    # Acompanhantes que também ocupam um leito do mesmo quarto do paciente
    # (`EstadiaAcompanhante.ocupa_leito`) — ainda presentes (`data_saida`
    # nulo) e cuja estadia do paciente segue "Em acompanhamento". Entram no
    # mesmo pool de ocupantes do quarto, disputando os `leito` lugares
    # junto com o(s) titular(es) — mesma heurística de excedente vira
    # `pendentes_revisao`.
    linhas_acompanhante = db.execute(
        select(
            Estadia.id,
            Estadia.id_quarto,
            EstadiaAcompanhante.id_pessoa,
            EstadiaAcompanhante.data_entrada,
            Pessoa.nome,
        )
        .join(Estadia, Estadia.id == EstadiaAcompanhante.id_estadia)
        .join(Pessoa, Pessoa.id == EstadiaAcompanhante.id_pessoa)
        .where(
            EstadiaAcompanhante.ocupa_leito.is_(True),
            EstadiaAcompanhante.data_saida.is_(None),
            Estadia.situacao == SituacaoEstadia.EM_ACOMPANHAMENTO,
        )
    ).all()
    for id_estadia, id_quarto, id_pessoa, data_entrada, nome_pessoa in linhas_acompanhante:
        por_quarto.setdefault(id_quarto, []).append(
            {
                "id_estadia": id_estadia,
                "id_pessoa": id_pessoa,
                "nome_pessoa": nome_pessoa,
                "data_entrada": data_entrada,
                "acompanhante": True,
            }
        )

    resultado = []
    for quarto in quartos:
        todas = sorted(por_quarto.get(quarto.id, []), key=lambda linha: linha["data_entrada"], reverse=True)
        resultado.append(
            {
                "id": quarto.id,
                "numero": quarto.numero,
                "descricao": quarto.descricao,
                "leito": quarto.leito,
                "ocupantes": todas[: quarto.leito],
                "pendentes_revisao": todas[quarto.leito :],
            }
        )
    return resultado


def buscar(db: Session, quarto_id: int) -> Quarto | None:
    return db.get(Quarto, quarto_id)


def criar(db: Session, dados: QuartoCreate) -> Quarto:
    quarto = Quarto(**dados.model_dump())
    db.add(quarto)
    db.commit()
    db.refresh(quarto)
    return quarto


def atualizar(db: Session, quarto: Quarto, dados: QuartoUpdate) -> Quarto:
    for campo, valor in dados.model_dump().items():
        setattr(quarto, campo, valor)
    db.commit()
    db.refresh(quarto)
    return quarto


def inativar(db: Session, quarto: Quarto) -> None:
    quarto.ativo = False
    db.commit()
