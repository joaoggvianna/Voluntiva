"""Notificações entregues por WebSocket (web) e push VAP (clientes TCP)."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TipoNotificacao

_tipo_notificacao = PGEnum(
    TipoNotificacao, name="tipo_notificacao", create_type=False,
    values_callable=lambda e: [m.value for m in e],
)


class Notificacao(Base):
    __tablename__ = "notificacao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    acao_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("acao_social.id", ondelete="CASCADE"))
    tipo: Mapped[TipoNotificacao] = mapped_column(_tipo_notificacao, nullable=False)
    titulo: Mapped[str] = mapped_column(String(160), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    lida: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    criada_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
