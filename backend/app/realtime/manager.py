"""Registro de conexões WebSocket ativas, por usuário.

Guarda tudo em memória: com mais de uma réplica da API isso deixa de
funcionar e precisa migrar para Redis pub/sub ou LISTEN/NOTIFY do Postgres.
Para o escopo do projeto (uma instância) é suficiente.
"""
import asyncio
import uuid
from collections import defaultdict

from fastapi import WebSocket


class GerenciadorConexoes:
    def __init__(self) -> None:
        self._conexoes: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def conectar(self, usuario_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._conexoes[usuario_id].add(ws)

    async def desconectar(self, usuario_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._conexoes[usuario_id].discard(ws)
            if not self._conexoes[usuario_id]:
                del self._conexoes[usuario_id]

    async def enviar_para(self, usuario_id: uuid.UUID, mensagem: dict) -> None:
        async with self._lock:
            destinos = list(self._conexoes.get(usuario_id, ()))
        for ws in destinos:
            try:
                await ws.send_json(mensagem)
            except Exception:
                # Conexão morta: remove sem derrubar o envio aos demais.
                await self.desconectar(usuario_id, ws)

    async def broadcast(self, mensagem: dict) -> None:
        async with self._lock:
            pares = [(uid, ws) for uid, wss in self._conexoes.items() for ws in wss]
        for usuario_id, ws in pares:
            try:
                await ws.send_json(mensagem)
            except Exception:
                await self.desconectar(usuario_id, ws)

    @property
    def total_conexoes(self) -> int:
        return sum(len(w) for w in self._conexoes.values())


gerenciador = GerenciadorConexoes()
