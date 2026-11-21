"""Perfil do voluntário autenticado, catálogo de habilidades e histórico."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_tipo
from app.core.exceptions import DadosInvalidos, RecursoNaoEncontrado
from app.db.session import get_db
from app.models import TipoUsuario, Usuario
from app.schemas.voluntario import (
    HabilidadeResponse,
    Historico,
    PerfilUpdate,
    PerfilVoluntario,
)
from app.services import voluntario_service

router = APIRouter(tags=["voluntários"])

_VOLUNTARIO = Depends(exigir_tipo(TipoUsuario.VOLUNTARIO))


@router.get("/habilidades", response_model=list[HabilidadeResponse])
def listar_habilidades(db: Session = Depends(get_db)):
    """Catálogo controlado de habilidades (público)."""
    return voluntario_service.listar_habilidades(db)


@router.get("/voluntarios/eu", response_model=PerfilVoluntario)
def obter_perfil(db: Session = Depends(get_db), usuario: Usuario = _VOLUNTARIO):
    try:
        return voluntario_service.obter_perfil(db, usuario)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)


@router.put("/voluntarios/eu", response_model=PerfilVoluntario)
def atualizar_perfil(
    dados: PerfilUpdate, db: Session = Depends(get_db), usuario: Usuario = _VOLUNTARIO
):
    try:
        return voluntario_service.atualizar_perfil(db, usuario, dados)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
    except DadosInvalidos as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.mensagem)


@router.get("/voluntarios/eu/historico", response_model=Historico)
def historico(db: Session = Depends(get_db), usuario: Usuario = _VOLUNTARIO):
    try:
        return voluntario_service.historico(db, usuario)
    except RecursoNaoEncontrado as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
