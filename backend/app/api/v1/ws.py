"""Canal WebSocket de notificações."""
import asyncio
import uuid

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from starlette.concurrency import run_in_threadpool

from app.core.security import decodificar_token
from app.db.session import SessionLocal
from app.models import Usuario
from app.realtime import gerenciador

router = APIRouter(tags=["tempo real"])

# Prazo para o cliente mandar o token depois de abrir a conexão.
PRAZO_AUTENTICACAO = 10


def _usuario_ativo(usuario_id: uuid.UUID) -> bool:
    """Como na API REST: conta desativada perde o canal na hora, sem
    esperar o token expirar."""
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, usuario_id)
        return usuario is not None and usuario.ativo
    finally:
        db.close()


async def _autenticar(token: str) -> uuid.UUID | None:
    try:
        payload = decodificar_token(token, scope_esperado="access")
        usuario_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
    if not await run_in_threadpool(_usuario_ativo, usuario_id):
        return None
    return usuario_id


@router.websocket("/ws/notificacoes")
async def notificacoes(websocket: WebSocket):
    """O token vai na PRIMEIRA MENSAGEM depois de abrir a conexão, e não
    na query string: a URL do handshake aparece no log de acesso do
    servidor (e do proxy do Render), e um token ali ficaria gravado em
    texto claro. A API WebSocket do navegador não permite cabeçalhos, por
    isso a mensagem. Em produção a conexão é sempre wss://.
    """
    await websocket.accept()
    try:
        token = await asyncio.wait_for(websocket.receive_text(), PRAZO_AUTENTICACAO)
    except (asyncio.TimeoutError, WebSocketDisconnect):
        await _fechar(websocket)
        return

    usuario_id = await _autenticar(token)
    if usuario_id is None:
        await _fechar(websocket)
        return

    await gerenciador.conectar(usuario_id, websocket)
    try:
        while True:
            # Mantém a conexão viva e responde ao heartbeat do cliente.
            mensagem = await websocket.receive_text()
            if mensagem == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        await gerenciador.desconectar(usuario_id, websocket)


async def _fechar(websocket: WebSocket) -> None:
    try:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except RuntimeError:
        pass  # o cliente já tinha fechado
