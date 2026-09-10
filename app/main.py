from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.features.auth.router import router as auth_router
from app.features.pessoas.router import router as pessoas_router

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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
