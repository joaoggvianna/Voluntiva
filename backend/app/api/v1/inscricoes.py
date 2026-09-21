"""Rotas de inscrição e presença."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import usuario_atual
from app.core.exceptions import ConflitoDeEstado, RecursoNaoEncontrado
from app.db.session import get_db
from app.models import Usuario
from app.schemas.inscricao import (
    InscricaoCancel,
    InscricaoCreate,
    InscricaoResponse,
    PresencaResponse,
)
from app.services import inscricao_service

router = APIRouter(prefix="/inscricoes", tags=["inscrições"])


@router.post("", response_model=InscricaoResponse, status_code=status.HTTP_201_CREATED)
def inscrever(
    dados: InscricaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        return inscricao_service.inscrever(db, usuario.id, dados.acao_id)
    except ConflitoDeEstado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)


@router.delete("/{acao_id}", response_model=InscricaoResponse)
def cancelar(
    acao_id: uuid.UUID,
    dados: InscricaoCancel | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        return inscricao_service.cancelar(
            db, usuario.id, acao_id, motivo=dados.motivo if dados else None
        )
    except ConflitoDeEstado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)


@router.post("/{inscricao_id}/check-in", response_model=PresencaResponse, status_code=201)
def check_in(
    inscricao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        return inscricao_service.check_in(db, inscricao_id, registrado_por=usuario.id)
    except ConflitoDeEstado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)


@router.post("/{inscricao_id}/check-out", response_model=PresencaResponse)
def check_out(
    inscricao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    try:
        return inscricao_service.check_out(db, inscricao_id)
    except ConflitoDeEstado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
