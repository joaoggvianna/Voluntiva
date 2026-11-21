"""Autorização das rotas de ONG (ações, unidades, presença).

A regra em si fica em app/services/permissao.py, compartilhada com o
servidor VAP; aqui ela só vira HTTP 403/422.
"""
import uuid
from collections.abc import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AcaoSocial, PapelMembro, TipoUsuario, Unidade, Usuario
from app.services import permissao

# Papéis que administram a organização (dados da ONG e unidades).
# `operador` opera ações e presença, mas não muda a estrutura da ONG.
PAPEIS_GESTAO = frozenset({PapelMembro.PROPRIETARIO, PapelMembro.GESTOR})


def exigir_acesso_ong(
    db: Session,
    usuario: Usuario,
    ong_id: uuid.UUID,
    unidade_id: uuid.UUID | None = None,
    *,
    papeis: Iterable[PapelMembro] | None = None,
) -> None:
    """Exige vínculo que cubra a ONG (unidade_id=None) ou a unidade dada.
    Com `papeis`, o vínculo também precisa ter um desses papéis."""
    if usuario.tipo not in (TipoUsuario.ADMIN, TipoUsuario.ONG):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Perfil sem permissão para esta operação")
    if not permissao.tem_acesso_ong(db, usuario.id, usuario.tipo, ong_id, unidade_id, papeis):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário não pertence à ONG/unidade desta ação")


def e_membro_da_ong(db: Session, usuario: Usuario | None, ong_id: uuid.UUID) -> bool:
    """Qualquer vínculo com a ONG (inteira ou de uma unidade), ou admin."""
    if usuario is None:
        return False
    if usuario.tipo == TipoUsuario.ADMIN:
        return True
    if usuario.tipo != TipoUsuario.ONG:
        return False
    return bool(permissao.vinculos(db, usuario.id, ong_id))


def exigir_unidade_da_ong(db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID | None) -> None:
    if unidade_id is None:
        return
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.ong_id != ong_id or not unidade.ativo:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unidade inválida para esta ONG")


def exigir_acesso_acao(db: Session, usuario: Usuario, acao: AcaoSocial) -> None:
    exigir_acesso_ong(db, usuario, acao.ong_id, acao.unidade_id)
