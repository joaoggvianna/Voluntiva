"""Notificações do usuário autenticado.

A entrega em tempo real é pelo WebSocket /ws/notificacoes; estas rotas
servem para carregar o que chegou enquanto o usuário estava desconectado
e para marcar como lidas.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import usuario_atual
from app.core.exceptions import RecursoNaoEncontrado
from app.db.session import get_db
from app.models import Usuario
from app.schemas.notificacao import (
    ContagemNaoLidas,
    MarcadasComoLidas,
    NotificacaoResponse,
)
from app.services import notificacao_service

router = APIRouter(prefix="/notificacoes", tags=["notificações"])


@router.get("", response_model=list[NotificacaoResponse])
def listar(
    apenas_nao_lidas: bool = False,
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    return notificacao_service.listar(
        db, usuario.id, apenas_nao_lidas=apenas_nao_lidas, limite=limite, offset=offset
    )


@router.get("/nao-lidas", response_model=ContagemNaoLidas)
def contar_nao_lidas(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)):
    return {"nao_lidas": notificacao_service.contar_nao_lidas(db, usuario.id)}


@router.post("/lidas", response_model=MarcadasComoLidas)
def marcar_todas_lidas(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)):
    return {"marcadas": notificacao_service.marcar_todas_lidas(db, usuario.id)}


@router.post("/{notificacao_id}/lida", response_model=NotificacaoResponse)
def marcar_lida(
    notificacao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        return notificacao_service.marcar_lida(db, usuario.id, notificacao_id)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
