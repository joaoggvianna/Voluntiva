"""Autorização de operações de ONG (ações, unidades, presença).

O tipo de conta ONG não concede acesso automático a outras organizações:
o acesso vem do vínculo em `ong_membro`.
  * vínculo com unidade_id NULL  -> ONG inteira
  * vínculo com unidade_id       -> só aquela unidade
Admin tem acesso a tudo.
"""
import uuid
from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcaoSocial, OngMembro, PapelMembro, TipoUsuario, Unidade, Usuario

# Papéis que administram a organização (dados da ONG e unidades).
# `operador` opera ações e presença, mas não muda a estrutura da ONG.
PAPEIS_GESTAO = frozenset({PapelMembro.PROPRIETARIO, PapelMembro.GESTOR})


def _vinculos(db: Session, usuario: Usuario, ong_id: uuid.UUID) -> list[OngMembro]:
    return list(db.scalars(
        select(OngMembro).where(
            OngMembro.usuario_id == usuario.id, OngMembro.ong_id == ong_id
        )
    ).all())


def exigir_acesso_ong(
    db: Session,
    usuario: Usuario,
    ong_id: uuid.UUID,
    unidade_id: uuid.UUID | None = None,
    *,
    papeis: Iterable[PapelMembro] | None = None,
) -> None:
    """Exige vínculo que cubra a ONG (unidade_id=None) ou a unidade dada.

    Com `papeis`, o vínculo que dá o acesso também precisa ter um desses
    papéis.
    """
    if usuario.tipo == TipoUsuario.ADMIN:
        return
    if usuario.tipo != TipoUsuario.ONG:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Perfil sem permissão para esta operação")

    permitidos = frozenset(papeis) if papeis is not None else None
    for vinculo in _vinculos(db, usuario, ong_id):
        cobre = vinculo.unidade_id is None or vinculo.unidade_id == unidade_id
        if cobre and (permitidos is None or vinculo.papel in permitidos):
            return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário não pertence à ONG/unidade desta ação")


def e_membro_da_ong(db: Session, usuario: Usuario | None, ong_id: uuid.UUID) -> bool:
    """Qualquer vínculo com a ONG (inteira ou de uma unidade), ou admin."""
    if usuario is None:
        return False
    if usuario.tipo == TipoUsuario.ADMIN:
        return True
    if usuario.tipo != TipoUsuario.ONG:
        return False
    return bool(_vinculos(db, usuario, ong_id))


def exigir_unidade_da_ong(db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID | None) -> None:
    if unidade_id is None:
        return
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.ong_id != ong_id or not unidade.ativo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unidade inválida para esta ONG")


def exigir_acesso_acao(db: Session, usuario: Usuario, acao: AcaoSocial) -> None:
    exigir_acesso_ong(db, usuario, acao.ong_id, acao.unidade_id)
