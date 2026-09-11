from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.avaliacao_social.models import AvaliacaoSocial
from app.features.avaliacao_social.schemas import AvaliacaoSocialCreate, AvaliacaoSocialUpdate


def listar_por_pessoa(db: Session, pessoa_id: int) -> list[AvaliacaoSocial]:
    consulta = select(AvaliacaoSocial).where(AvaliacaoSocial.id_pessoa == pessoa_id)
    return list(db.scalars(consulta.order_by(AvaliacaoSocial.data_movimento.desc())).all())


def buscar(db: Session, avaliacao_id: int) -> AvaliacaoSocial | None:
    return db.get(AvaliacaoSocial, avaliacao_id)


def criar(db: Session, pessoa_id: int, dados: AvaliacaoSocialCreate) -> AvaliacaoSocial:
    avaliacao = AvaliacaoSocial(id_pessoa=pessoa_id, **dados.model_dump())
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


def atualizar(
    db: Session, avaliacao: AvaliacaoSocial, dados: AvaliacaoSocialUpdate
) -> AvaliacaoSocial:
    for campo, valor in dados.model_dump().items():
        setattr(avaliacao, campo, valor)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao
