"""Canal WebSocket de notificações."""
import uuid

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.security import decodificar_token
from app.realtime import gerenciador

router = APIRouter(tags=["tempo real"])


@router.websocket("/ws/notificacoes")
async def notificacoes(websocket: WebSocket, token: str = Query(...)):
    """O token vai por query string porque a API WebSocket do navegador
    não permite definir cabeçalhos. Por isso é obrigatório usar wss://
    em produção — em ws:// o token trafega em claro.
    """
    try:
        payload = decodificar_token(token, scope_esperado="access")
        usuario_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
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
