from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.materiais import service
from app.features.materiais.schemas import (
    MaterialCreate,
    MaterialResponse,
    MaterialResumoResponse,
    MaterialUpdate,
)

router = APIRouter()


@router.get("")
def listar(
    busca: str | None = None,
    apenas_disponiveis_emprestimo: bool = False,
    skip: int = 0,
    take: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    itens, total = service.listar(
        db,
        busca=busca,
        apenas_disponiveis_emprestimo=apenas_disponiveis_emprestimo,
        skip=skip,
        take=take,
    )
    return {"items": [MaterialResumoResponse.model_validate(m) for m in itens], "total": total}


@router.get("/{material_id}", response_model=MaterialResponse)
def buscar(material_id: int, db: Session = Depends(get_db)) -> MaterialResponse:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    return MaterialResponse.model_validate(material)


@router.post("", response_model=MaterialResponse, status_code=201)
def criar(dados: MaterialCreate, db: Session = Depends(get_db)) -> MaterialResponse:
    return MaterialResponse.model_validate(service.criar(db, dados))


@router.put("/{material_id}", response_model=MaterialResponse)
def atualizar(material_id: int, dados: MaterialUpdate, db: Session = Depends(get_db)) -> MaterialResponse:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    return MaterialResponse.model_validate(service.atualizar(db, material, dados))


@router.delete("/{material_id}", status_code=204)
def inativar(material_id: int, db: Session = Depends(get_db)) -> None:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    service.inativar(db, material)


@router.get("/{material_id}/foto")
def obter_foto(material_id: int, db: Session = Depends(get_db)) -> Response:
    material = service.buscar(db, material_id)
    if material is None or material.foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    return Response(content=material.foto, media_type=material.foto_content_type or "image/jpeg")


@router.get("/{material_id}/foto/thumb")
def obter_foto_thumb(material_id: int, db: Session = Depends(get_db)) -> Response:
    material = service.buscar(db, material_id)
    if material is None or material.foto_thumb is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    return Response(content=material.foto_thumb, media_type=material.foto_content_type or "image/jpeg")


@router.put("/{material_id}/foto", response_model=MaterialResponse)
def salvar_foto(
    material_id: int, arquivo: UploadFile = File(...), db: Session = Depends(get_db)
) -> MaterialResponse:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")

    conteudo = arquivo.file.read()
    try:
        material = service.salvar_foto(db, material, conteudo, arquivo.content_type)
    except service.FotoInvalida as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MaterialResponse.model_validate(material)


@router.delete("/{material_id}/foto", status_code=204)
def remover_foto(material_id: int, db: Session = Depends(get_db)) -> None:
    material = service.buscar(db, material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    service.remover_foto(db, material)
