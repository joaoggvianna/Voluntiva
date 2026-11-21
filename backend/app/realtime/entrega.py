"""Entrega, pelo WebSocket, das notificações gravadas numa requisição.

Os services gravam as notificações na transação e as anotam em
`db.info[PENDENTES]` (ver notificacao_service). Depois que o service
comitou, a rota chama `agendar_entrega`, que agenda o envio como
BackgroundTask: roda depois da resposta, fora da transação, e uma falha
de envio não desfaz nada no banco (a notificação continua lá para ser
lida por GET /notificacoes).
"""
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.realtime.manager import gerenciador
from app.schemas.notificacao import NotificacaoResponse
from app.services.notificacao_service import PENDENTES


def agendar_entrega(db: Session, tarefas: BackgroundTasks) -> int:
    """Agenda o envio e devolve quantas notificações foram agendadas."""
    pendentes = db.info.pop(PENDENTES, [])
    if pendentes:
        tarefas.add_task(entregar, pendentes)
    return len(pendentes)


async def entregar(pendentes: list[dict]) -> None:
    for linha in pendentes:
        mensagem = NotificacaoResponse.model_validate(linha).model_dump(mode="json")
        await gerenciador.enviar_para(linha["usuario_id"], mensagem)
