from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.estadias.models import Estadia, SituacaoEstadia
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
        select(Estadia.id, Estadia.id_quarto, Estadia.id_pessoa, Estadia.data_entrada, Pessoa.nome)
        .join(Pessoa, Pessoa.id == Estadia.id_pessoa)
        .where(Estadia.situacao == SituacaoEstadia.EM_ACOMPANHAMENTO)
        .order_by(Estadia.id_quarto, Estadia.data_entrada.desc())
    ).all()

    por_quarto: dict[int, list[dict]] = {}
    for id_estadia, id_quarto, id_pessoa, data_entrada, nome_pessoa in linhas:
        por_quarto.setdefault(id_quarto, []).append(
            {
                "id_estadia": id_estadia,
                "id_pessoa": id_pessoa,
                "nome_pessoa": nome_pessoa,
                "data_entrada": data_entrada,
            }
        )

    resultado = []
    for quarto in quartos:
        todas = por_quarto.get(quarto.id, [])
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
