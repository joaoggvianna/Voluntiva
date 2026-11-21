"""Rotas de inscrição e presença."""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.autorizacao import exigir_acesso_acao
from app.api.deps import exigir_tipo, usuario_atual
from app.core.exceptions import ConflitoDeEstado, RecursoNaoEncontrado
from app.db.session import get_db
from app.models import AcaoSocial, Inscricao, TipoUsuario, Usuario
from app.realtime.entrega import agendar_entrega
from app.schemas.inscricao import (
    InscricaoCancel,
    InscricaoComAcao,
    InscricaoCreate,
    InscricaoResponse,
    PresencaResponse,
)
from app.services import inscricao_service

router = APIRouter(prefix="/inscricoes", tags=["inscrições"])


def _erro_http(exc: Exception) -> HTTPException:
    if isinstance(exc, RecursoNaoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
    return HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)


def _acao_gerida(db: Session, usuario: Usuario, inscricao_id: uuid.UUID) -> None:
    """Check-in/out só por quem gere a ação da inscrição."""
    inscricao = db.get(Inscricao, inscricao_id)
    if inscricao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inscrição não encontrada")
    acao = db.get(AcaoSocial, inscricao.acao_id)
    if acao is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ação social não encontrada")
    exigir_acesso_acao(db, usuario, acao)


@router.get("/minhas", response_model=list[InscricaoComAcao])
def minhas(
    incluir_canceladas: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    """Inscrições do voluntário autenticado, com a ação e a presença."""
    return inscricao_service.listar_do_voluntario(
        db, usuario.id, incluir_canceladas=incluir_canceladas
    )


@router.post("", response_model=InscricaoResponse, status_code=status.HTTP_201_CREATED)
def inscrever(
    dados: InscricaoCreate,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.VOLUNTARIO)),
):
    try:
        inscricao = inscricao_service.inscrever(db, usuario.id, dados.acao_id)
    except (ConflitoDeEstado, RecursoNaoEncontrado) as exc:
        raise _erro_http(exc)
    agendar_entrega(db, tarefas)
    return inscricao


@router.delete("/{acao_id}", response_model=InscricaoResponse)
def cancelar(
    acao_id: uuid.UUID,
    tarefas: BackgroundTasks,
    dados: InscricaoCancel | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.VOLUNTARIO)),
):
    try:
        inscricao = inscricao_service.cancelar(
            db, usuario.id, acao_id, motivo=dados.motivo if dados else None
        )
    except (ConflitoDeEstado, RecursoNaoEncontrado) as exc:
        raise _erro_http(exc)
    agendar_entrega(db, tarefas)
    return inscricao


@router.post("/{inscricao_id}/check-in", response_model=PresencaResponse, status_code=201)
def check_in(
    inscricao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    _acao_gerida(db, usuario, inscricao_id)
    try:
        return inscricao_service.check_in(db, inscricao_id, registrado_por=usuario.id)
    except (ConflitoDeEstado, RecursoNaoEncontrado) as exc:
        raise _erro_http(exc)


@router.post("/{inscricao_id}/check-out", response_model=PresencaResponse)
def check_out(
    inscricao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_atual),
):
    _acao_gerida(db, usuario, inscricao_id)
    try:
        return inscricao_service.check_out(db, inscricao_id)
    except (ConflitoDeEstado, RecursoNaoEncontrado) as exc:
        raise _erro_http(exc)
