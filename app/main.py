from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.features.auth.router import router as auth_router
from app.features.avaliacao_social.router import router as avaliacao_social_router
from app.features.composicao_familiar.router import router as composicao_familiar_router
from app.features.estadias.router import router as estadias_router
from app.features.emprestimos.router import router as emprestimos_router
from app.features.estados.router import router as estados_router
from app.features.materiais.router import router as materiais_router
from app.features.hospitais.router import router as hospitais_router
from app.features.municipios.router import router as municipios_router
from app.features.pessoas.router import router as pessoas_router
from app.features.quartos.router import router as quartos_router
from app.features.voluntarios.router import router as voluntarios_router

app = FastAPI(title="Abrigo — Casa de Apoio Amor Fraterno", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(pessoas_router, prefix="/api/pessoas", tags=["pessoas"])
app.include_router(estados_router, prefix="/api/estados", tags=["estados"])
app.include_router(municipios_router, prefix="/api/municipios", tags=["municipios"])
app.include_router(hospitais_router, prefix="/api/hospitais", tags=["hospitais"])
app.include_router(quartos_router, prefix="/api/quartos", tags=["quartos"])
app.include_router(estadias_router, prefix="/api/estadias", tags=["estadias"])
app.include_router(voluntarios_router, prefix="/api/voluntarios", tags=["voluntarios"])
app.include_router(materiais_router, prefix="/api/materiais", tags=["materiais"])
app.include_router(emprestimos_router, prefix="/api/emprestimos", tags=["emprestimos"])
app.include_router(
    avaliacao_social_router,
    prefix="/api/pessoas/{pessoa_id}/avaliacoes-sociais",
    tags=["avaliacao-social"],
)
app.include_router(
    composicao_familiar_router,
    prefix="/api/pessoas/{pessoa_id}/composicao-familiar",
    tags=["composicao-familiar"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
