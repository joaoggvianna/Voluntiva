"""Modelos de organização, unidade e vínculo de membro."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PapelMembro

_papel_membro = PGEnum(
    PapelMembro, name="papel_membro", create_type=False,
    values_callable=lambda e: [m.value for m in e],
)


class Ong(Base):
    __tablename__ = "ong"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    cnpj: Mapped[str | None] = mapped_column(String(14))
    email_contato: Mapped[str | None] = mapped_column(String(320))
    telefone: Mapped[str | None] = mapped_column(String(13))
    descricao: Mapped[str | None] = mapped_column(Text)
    site: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    unidades: Mapped[list[Unidade]] = relationship(back_populates="ong", cascade="all, delete-orphan")
    membros: Mapped[list[OngMembro]] = relationship(back_populates="ong", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Ong {self.nome}>"


class Unidade(Base):
    __tablename__ = "unidade"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    ong_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ong.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(200))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(100))
    bairro: Mapped[str | None] = mapped_column(String(100))
    cidade: Mapped[str] = mapped_column(String(120), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ong: Mapped[Ong] = relationship(back_populates="unidades")


class OngMembro(Base):
    """Vínculo usuário <-> ONG.

    unidade_id NULL  = acesso a toda a ONG      (Cliente ONG)
    unidade_id != NULL = acesso a uma unidade   (Cliente Unidade)
    """
    __tablename__ = "ong_membro"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    usuario_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    ong_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("ong.id", ondelete="CASCADE"), nullable=False)
    unidade_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("unidade.id", ondelete="CASCADE"))
    papel: Mapped[PapelMembro] = mapped_column(_papel_membro, nullable=False, server_default="operador")
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ong: Mapped[Ong] = relationship(back_populates="membros")
