"""Rotas de ações sociais."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_tipo, usuario_atual
from app.core.exceptions import RecursoNaoEncontrado
from app.db.session import get_db
from app.models import StatusAcao, TipoUsuario, Usuario
from app.schemas.acao import AcaoCreate, AcaoResponse, AcaoUpdate
from app.services import acao_service

router = APIRouter(prefix="/acoes", tags=["ações sociais"])


@router.get("")
def listar(
    db: Session = Depends(get_db),
    status_filtro: StatusAcao | None = Query(default=StatusAcao.PUBLICADA, alias="status"),
    ong_id: uuid.UUID | None = None,
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return acao_service.listar_com_vagas(
        db, status=status_filtro, ong_id=ong_id, limite=limite, offset=offset
    )


@router.get("/{acao_id}", response_model=AcaoResponse)
def obter(acao_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return acao_service.obter(db, acao_id)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)


@router.post("", response_model=AcaoResponse, status_code=status.HTTP_201_CREATED)
def criar(
    dados: AcaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN)),
):
    # TODO(equipe): confirmar via ong_membro que este usuário pertence a dados.ong_id.
    return acao_service.criar(db, dados, criado_por=usuario.id)


@router.patch("/{acao_id}", response_model=AcaoResponse)
def atualizar(
    acao_id: uuid.UUID,
    dados: AcaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN)),
):
    try:
        return acao_service.atualizar(db, acao_id, dados)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
