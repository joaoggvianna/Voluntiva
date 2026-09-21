# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# PYTHONUNBUFFERED: logs saem na hora, sem ficar presos no buffer —
# sem isso o `docker compose logs` fica mudo durante a execução.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq5 é o runtime do psycopg; build-essential só para compilar argon2-cffi
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements antes do código: o Docker reaproveita a camada de
# dependências enquanto o requirements.txt não mudar.
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt

COPY . .

# Nunca rodar como root dentro do container.
RUN useradd --create-home --uid 1000 voluntiva && chown -R voluntiva:voluntiva /app
USER voluntiva

EXPOSE 8000 9009

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
