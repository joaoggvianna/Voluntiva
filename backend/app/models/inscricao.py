"""Inscrições em ações e registro de presença."""
from __future__ import annotations

import datetime as dt
import decimal
import uuid

from sqlalchemy import DateTime, FetchedValue, ForeignKey, Numeric, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusInscricao

_status_inscricao = PGEnum(
    StatusInscricao, name="status_inscricao", create_type=False,
    values_callable=lambda e: [m.value for m in e],
)


class Inscricao(Base):
    """UNIQUE (acao_id, voluntario_id) no banco impede inscrição duplicada.

    O controle de lotação é feito por trigger com SELECT ... FOR UPDATE,
    não aqui: validar em Python abriria race condition entre requisições
    HTTP concorrentes e conexões TCP simultâneas.
    """
    __tablename__ = "inscricao"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    acao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("acao_social.id", ondelete="CASCADE"), nullable=False
    )
    voluntario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("voluntario.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[StatusInscricao] = mapped_column(
        _status_inscricao, nullable=False, server_default="pendente"
    )
    inscrito_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelado_em: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cancelamento: Mapped[str | None] = mapped_column(Text)

    presenca: Mapped[Presenca | None] = relationship(
        back_populates="inscricao", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Inscricao {self.id} {self.status}>"


class Presenca(Base):
    """PK = inscricao_id: uma presença por inscrição, garantido pelo schema."""
    __tablename__ = "presenca"

    inscricao_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("inscricao.id", ondelete="CASCADE"), primary_key=True
    )
    check_in: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    registrado_por: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("usuario.id", ondelete="SET NULL")
    )
    observacao: Mapped[str | None] = mapped_column(Text)
    # Coluna GENERATED no banco: somente leitura, nunca atribuir em Python.
    horas_computadas: Mapped[decimal.Decimal | None] = mapped_column(
        Numeric(6, 2), server_default=FetchedValue(), server_onupdate=FetchedValue()
    )

    inscricao: Mapped[Inscricao] = relationship(back_populates="presenca")
