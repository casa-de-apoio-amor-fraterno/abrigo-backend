import io

from PIL import Image
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.features.materiais.models import Material
from app.features.materiais.schemas import MaterialCreate, MaterialUpdate


def listar(
    db: Session,
    busca: str | None = None,
    apenas_disponiveis_emprestimo: bool = False,
    skip: int = 0,
    take: int = 50,
) -> tuple[list[Material], int]:
    consulta = select(Material).where(Material.ativo.is_not(False))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(
            or_(Material.descricao.ilike(termo), Material.codigo_identificacao.ilike(termo))
        )
    if apenas_disponiveis_emprestimo:
        consulta = consulta.where(Material.disponivel_emprestimo.is_(True))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    itens = db.scalars(consulta.order_by(Material.descricao).offset(skip).limit(take)).all()
    return list(itens), total


def buscar(db: Session, material_id: int) -> Material | None:
    return db.get(Material, material_id)


def criar(db: Session, dados: MaterialCreate) -> Material:
    material = Material(**dados.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def atualizar(db: Session, material: Material, dados: MaterialUpdate) -> Material:
    for campo, valor in dados.model_dump().items():
        setattr(material, campo, valor)
    db.commit()
    db.refresh(material)
    return material


def inativar(db: Session, material: Material) -> None:
    material.ativo = False
    db.commit()


TIPOS_FOTO_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
TAMANHO_MAXIMO_FOTO_BYTES = 5 * 1024 * 1024
TAMANHO_THUMB = (200, 200)
_FORMATO_PIL_POR_CONTENT_TYPE = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


class FotoInvalida(Exception):
    pass


def _gerar_thumbnail(conteudo: bytes, content_type: str) -> bytes:
    imagem = Image.open(io.BytesIO(conteudo))
    imagem.thumbnail(TAMANHO_THUMB)
    formato = _FORMATO_PIL_POR_CONTENT_TYPE[content_type]
    if formato == "JPEG" and imagem.mode in ("RGBA", "P"):
        # JPEG não suporta transparência — achata sobre fundo branco antes
        # de converter, senão o Pillow lança erro ao salvar.
        imagem = imagem.convert("RGB")
    buffer = io.BytesIO()
    imagem.save(buffer, format=formato)
    return buffer.getvalue()


def salvar_foto(db: Session, material: Material, conteudo: bytes, content_type: str | None) -> Material:
    if content_type not in TIPOS_FOTO_PERMITIDOS:
        raise FotoInvalida("Formato de imagem não suportado — envie JPEG, PNG ou WebP.")
    if len(conteudo) > TAMANHO_MAXIMO_FOTO_BYTES:
        raise FotoInvalida("Imagem maior que o limite permitido (5MB).")

    try:
        thumb = _gerar_thumbnail(conteudo, content_type)
    except Exception as exc:
        # Content-type declarado bate com a whitelist, mas o conteúdo não é
        # uma imagem decodificável de verdade (arquivo corrompido ou
        # content-type forjado) — o Pillow lança várias exceções diferentes
        # dependendo do caso, não só `UnidentifiedImageError`.
        raise FotoInvalida("Não foi possível processar o arquivo como imagem.") from exc

    material.foto = conteudo
    material.foto_content_type = content_type
    material.foto_thumb = thumb
    db.commit()
    db.refresh(material)
    return material


def remover_foto(db: Session, material: Material) -> None:
    material.foto = None
    material.foto_content_type = None
    material.foto_thumb = None
    db.commit()
