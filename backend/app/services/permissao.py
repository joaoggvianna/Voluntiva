"""Regra de acesso de um usuário a uma ONG/unidade, sem transporte.

A API REST (app/api/autorizacao.py) e o servidor VAP
(protocol/services_db.py) usam esta mesma função e só traduzem o "não"
para o seu formato de erro (HTTP 403 / VAP FORBIDDEN).

  * admin: acesso a tudo;
  * conta de ONG: precisa de vínculo em ong_membro com unidade_id NULL
    (ONG inteira) ou igual à unidade pedida;
  * voluntário: nunca.
"""
import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OngMembro, PapelMembro, TipoUsuario


def vinculos(db: Session, usuario_id: uuid.UUID, ong_id: uuid.UUID) -> list[OngMembro]:
    return list(db.scalars(
        select(OngMembro).where(OngMembro.usuario_id == usuario_id, OngMembro.ong_id == ong_id)
    ).all())


def tem_acesso_ong(
    db: Session,
    usuario_id: uuid.UUID,
    tipo: TipoUsuario,
    ong_id: uuid.UUID,
    unidade_id: uuid.UUID | None = None,
    papeis: Iterable[PapelMembro] | None = None,
) -> bool:
    if tipo == TipoUsuario.ADMIN:
        return True
    if tipo != TipoUsuario.ONG:
        return False
    permitidos = frozenset(papeis) if papeis is not None else None
    for vinculo in vinculos(db, usuario_id, ong_id):
        cobre = vinculo.unidade_id is None or vinculo.unidade_id == unidade_id
        if cobre and (permitidos is None or vinculo.papel in permitidos):
            return True
    return False
