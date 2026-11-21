"""Schemas de notificação."""
import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoNotificacao


class NotificacaoResponse(BaseModel):
    """Mesmo formato na API e no WebSocket (frontend/src/types: Notificacao)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    acao_id: uuid.UUID | None
    tipo: TipoNotificacao
    titulo: str
    mensagem: str
    lida: bool
    criada_em: dt.datetime


class ContagemNaoLidas(BaseModel):
    nao_lidas: int


class MarcadasComoLidas(BaseModel):
    marcadas: int
