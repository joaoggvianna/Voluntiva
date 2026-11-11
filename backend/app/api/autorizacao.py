"""Autorização de operações em ações sociais.

O tipo de conta ONG não concede acesso automático a outras organizações.
Membros vinculados a uma unidade só podem operar ações daquela unidade.
"""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcaoSocial, OngMembro, TipoUsuario, Unidade, Usuario


def exigir_acesso_ong(
    db: Session, usuario: Usuario, ong_id: uuid.UUID, unidade_id: uuid.UUID | None = None
) -> None:
    if usuario.tipo == TipoUsuario.ADMIN:
        return
    if usuario.tipo != TipoUsuario.ONG:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Perfil sem permissão para esta operação")

    vinculos = db.scalars(
        select(OngMembro).where(
            OngMembro.usuario_id == usuario.id, OngMembro.ong_id == ong_id
        )
    ).all()
    if not any(v.unidade_id is None or v.unidade_id == unidade_id for v in vinculos):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário não pertence à ONG/unidade desta ação")


def exigir_unidade_da_ong(db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID | None) -> None:
    if unidade_id is None:
        return
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.ong_id != ong_id or not unidade.ativo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unidade inválida para esta ONG")


def exigir_acesso_acao(db: Session, usuario: Usuario, acao: AcaoSocial) -> None:
    exigir_acesso_ong(db, usuario, acao.ong_id, acao.unidade_id)
