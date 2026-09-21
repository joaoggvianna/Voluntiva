"""Modelos de identidade e perfil de voluntário."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, SmallInteger, String, Text, Time, Uuid, func
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import NivelHabilidade, TipoUsuario

# create_type=False: o tipo já existe no banco, criado pela migration.
# values_callable garante que o SQLAlchemy envie o VALOR ("voluntario")
# e não o NOME do membro ("VOLUNTARIO").
_tipo_usuario = PGEnum(
    TipoUsuario, name="tipo_usuario", create_type=False,
    values_callable=lambda e: [m.value for m in e],
)
_nivel_habilidade = PGEnum(
    NivelHabilidade, name="nivel_habilidade", create_type=False,
    values_callable=lambda e: [m.value for m in e],
)


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    # Hash Argon2id. Ver app/core/security.py — nunca guardar senha em claro.
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[TipoUsuario] = mapped_column(_tipo_usuario, nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    ultimo_login: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voluntario: Mapped[Voluntario | None] = relationship(back_populates="usuario", uselist=False)

    def __repr__(self) -> str:
        return f"<Usuario {self.email} ({self.tipo})>"


class Voluntario(Base):
    __tablename__ = "voluntario"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    telefone: Mapped[str | None] = mapped_column(String(13))
    data_nascimento: Mapped[dt.date | None] = mapped_column(Date)
    cidade: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[str | None] = mapped_column(String(2))
    biografia: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuario: Mapped[Usuario] = relationship(back_populates="voluntario")
    habilidades: Mapped[list[VoluntarioHabilidade]] = relationship(
        back_populates="voluntario", cascade="all, delete-orphan"
    )
    disponibilidades: Mapped[list[VoluntarioDisponibilidade]] = relationship(
        back_populates="voluntario", cascade="all, delete-orphan"
    )


class VoluntarioHabilidade(Base):
    __tablename__ = "voluntario_habilidade"

    voluntario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("voluntario.id", ondelete="CASCADE"), primary_key=True
    )
    habilidade_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("habilidade.id", ondelete="RESTRICT"), primary_key=True
    )
    nivel: Mapped[NivelHabilidade] = mapped_column(_nivel_habilidade, nullable=False, server_default="basico")
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    voluntario: Mapped[Voluntario] = relationship(back_populates="habilidades")
    habilidade: Mapped["Habilidade"] = relationship()  # noqa: F821


class VoluntarioDisponibilidade(Base):
    __tablename__ = "voluntario_disponibilidade"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    voluntario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("voluntario.id", ondelete="CASCADE"), nullable=False
    )
    # 0 = domingo ... 6 = sábado (mesma convenção de EXTRACT(DOW))
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[dt.time] = mapped_column(Time, nullable=False)
    hora_fim: Mapped[dt.time] = mapped_column(Time, nullable=False)

    voluntario: Mapped[Voluntario] = relationship(back_populates="disponibilidades")
