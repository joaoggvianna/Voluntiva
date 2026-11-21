"""Agrega as rotas da v1."""
from fastapi import APIRouter

from app.api.v1 import (
    acoes,
    auth,
    estatisticas,
    inscricoes,
    notificacoes,
    ongs,
    voluntarios,
    ws,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(acoes.router)
api_router.include_router(inscricoes.router)
api_router.include_router(ongs.router)
api_router.include_router(voluntarios.router)
api_router.include_router(notificacoes.router)
api_router.include_router(estatisticas.router)

# WebSocket fica fora do prefixo /api/v1 para a URL ser /ws/notificacoes
ws_router = APIRouter()
ws_router.include_router(ws.router)
