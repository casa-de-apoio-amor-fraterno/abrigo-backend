# Build multi-stage: o frontend (Angular) vive num repositório separado
# (abrigo-frontend) — clona e builda numa etapa própria com Node, depois
# copia só o resultado (HTML/JS/CSS estático) pra imagem final do backend,
# que serve tudo pela mesma porta (ver app/main.py, `_frontend_dist`).
# Pensado pro deploy de teste no Render (ver docs/deploy-render.md) — ainda
# não é a topologia definitiva de produção.

FROM node:20-slim AS frontend
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Repositório público (ver README) — sem credencial necessária pro clone.
RUN git clone --depth 1 https://github.com/casa-de-apoio-amor-fraterno/abrigo-frontend.git /frontend
WORKDIR /frontend
RUN npm ci && npm run build

FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /frontend/dist/abrigo-frontend/browser ./frontend-dist
ENV FRONTEND_DIST_DIR=/app/frontend-dist

# $PORT é injetado pelo Render em runtime (não fixo em build time).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
