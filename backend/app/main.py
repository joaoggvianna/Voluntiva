"""Ponto de entrada da API HTTP do Voluntiva.

Subir em desenvolvimento:
    uvicorn app.main:app --reload --port 8000

Documentação interativa: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router, ws_router
from app.core.config import settings
from app.core.exceptions import (
    ConflitoDeEstado,
    CredenciaisInvalidas,
    DadosInvalidos,
    PermissaoNegada,
    RecursoNaoEncontrado,
    UsuarioInativo,
    VoluntivaError,
)
from app.db.session import engine

# Mapeia exceção de domínio -> status HTTP. O servidor VAP tem o seu
# próprio mapeamento para códigos do protocolo, sobre os mesmos serviços.
_STATUS_POR_EXCECAO: dict[type[VoluntivaError], int] = {
    CredenciaisInvalidas: status.HTTP_401_UNAUTHORIZED,
    UsuarioInativo: status.HTTP_403_FORBIDDEN,
    PermissaoNegada: status.HTTP_403_FORBIDDEN,
    RecursoNaoEncontrado: status.HTTP_404_NOT_FOUND,
    ConflitoDeEstado: status.HTTP_409_CONFLICT,
    DadosInvalidos: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Falha rápido se o banco não responder: melhor não subir do que
    # aceitar requisições que vão estourar uma a uma.
    with engine.connect() as conexao:
        conexao.execute(text("SELECT 1"))
    yield
    engine.dispose()


app = FastAPI(
    title="Voluntiva API",
    description="Sistema de Gestão de Voluntários para ONGs",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(VoluntivaError)
async def _tratar_erro_dominio(request: Request, exc: VoluntivaError) -> JSONResponse:
    """Rede de segurança: pega exceções de domínio que escaparam da rota."""
    codigo = _STATUS_POR_EXCECAO.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(
        status_code=codigo,
        content={"erro": exc.codigo, "mensagem": exc.mensagem},
    )


@app.get("/health", tags=["infra"])
def health():
    """Usado pelo healthcheck do Docker Compose."""
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        banco = "ok"
    except Exception:
        banco = "indisponivel"
    return {"status": "ok", "banco": banco, "ambiente": settings.app_env}


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(ws_router)
