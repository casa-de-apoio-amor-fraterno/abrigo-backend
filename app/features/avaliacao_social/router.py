from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.auth.dependencies import exigir_perfil
from app.features.avaliacao_social import service
from app.features.avaliacao_social.schemas import (
    AvaliacaoSocialCreate,
    AvaliacaoSocialResponse,
    AvaliacaoSocialUpdate,
)

router = APIRouter(dependencies=[Depends(exigir_perfil("assistente_social"))])


@router.get("", response_model=list[AvaliacaoSocialResponse])
def listar(pessoa_id: int, db: Session = Depends(get_db)) -> list[AvaliacaoSocialResponse]:
    return [
        AvaliacaoSocialResponse.model_validate(a)
        for a in service.listar_por_pessoa(db, pessoa_id)
    ]


@router.post("", response_model=AvaliacaoSocialResponse, status_code=201)
def criar(
    pessoa_id: int, dados: AvaliacaoSocialCreate, db: Session = Depends(get_db)
) -> AvaliacaoSocialResponse:
    return AvaliacaoSocialResponse.model_validate(service.criar(db, pessoa_id, dados))


@router.put("/{avaliacao_id}", response_model=AvaliacaoSocialResponse)
def atualizar(
    pessoa_id: int,
    avaliacao_id: int,
    dados: AvaliacaoSocialUpdate,
    db: Session = Depends(get_db),
) -> AvaliacaoSocialResponse:
    avaliacao = service.buscar(db, avaliacao_id)
    if avaliacao is None or avaliacao.id_pessoa != pessoa_id:
        raise HTTPException(status_code=404, detail="Avaliação social não encontrada")
    return AvaliacaoSocialResponse.model_validate(service.atualizar(db, avaliacao, dados))
