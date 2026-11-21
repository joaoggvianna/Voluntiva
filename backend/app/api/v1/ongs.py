"""ONGs e unidades.

Públicas: cadastro de ONG, listagem e detalhe de ONGs e das unidades.
Restritas (vínculo em ong_membro): editar ONG, criar/editar/remover unidade.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.autorizacao import PAPEIS_GESTAO, exigir_acesso_ong
from app.api.deps import exigir_tipo, usuario_atual
from app.core.exceptions import ConflitoDeEstado, DadosInvalidos, RecursoNaoEncontrado
from app.db.session import get_db
from app.models import CausaSocial, TipoUsuario, Usuario
from app.schemas.auth import UsuarioPublico
from app.schemas.ong import (
    MinhaOng,
    OngCadastro,
    OngPublica,
    OngUpdate,
    UnidadeCreate,
    UnidadeResponse,
    UnidadeUpdate,
)
from app.services import ong_service

router = APIRouter(prefix="/ongs", tags=["ONGs"])

_GESTOR = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN))


def _erro_http(exc: Exception) -> HTTPException:
    if isinstance(exc, RecursoNaoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
    return HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)


@router.post("", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: OngCadastro, db: Session = Depends(get_db)):
    """Cadastro público de ONG. Depois, entrar com POST /auth/login."""
    try:
        return ong_service.cadastrar(db, dados)
    except DadosInvalidos as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)


@router.get("", response_model=list[OngPublica])
def listar(
    busca: str | None = Query(default=None, max_length=100),
    uf: str | None = Query(default=None, pattern=r"^[A-Z]{2}$"),
    causa: CausaSocial | None = None,
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return ong_service.listar_publicas(db, busca=busca, uf=uf, causa=causa, limite=limite, offset=offset)


@router.get("/minhas", response_model=list[MinhaOng])
def minhas_ongs(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)):
    """ONGs que o usuário gere, com as unidades a que tem acesso.
    Declarada antes de /{ong_id} para não ser capturada por ela."""
    return ong_service.minhas(db, usuario)


@router.get("/{ong_id}", response_model=OngPublica)
def obter(ong_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return ong_service.obter_publica(db, ong_id)
    except RecursoNaoEncontrado as exc:
        raise _erro_http(exc)


@router.patch("/{ong_id}", response_model=OngPublica)
def atualizar(
    ong_id: uuid.UUID,
    dados: OngUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = _GESTOR,
):
    exigir_acesso_ong(db, usuario, ong_id, None, papeis=PAPEIS_GESTAO)
    try:
        return ong_service.atualizar(db, ong_id, dados)
    except RecursoNaoEncontrado as exc:
        raise _erro_http(exc)


@router.get("/{ong_id}/unidades", response_model=list[UnidadeResponse])
def listar_unidades(ong_id: uuid.UUID, db: Session = Depends(get_db)):
    return ong_service.listar_unidades(db, ong_id)


@router.post(
    "/{ong_id}/unidades", response_model=UnidadeResponse, status_code=status.HTTP_201_CREATED
)
def criar_unidade(
    ong_id: uuid.UUID,
    dados: UnidadeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = _GESTOR,
):
    # Criar unidade exige gerir a ONG inteira, não só uma unidade.
    exigir_acesso_ong(db, usuario, ong_id, None, papeis=PAPEIS_GESTAO)
    try:
        return ong_service.criar_unidade(db, ong_id, dados)
    except (RecursoNaoEncontrado, ConflitoDeEstado) as exc:
        raise _erro_http(exc)


@router.patch("/{ong_id}/unidades/{unidade_id}", response_model=UnidadeResponse)
def atualizar_unidade(
    ong_id: uuid.UUID,
    unidade_id: uuid.UUID,
    dados: UnidadeUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = _GESTOR,
):
    # Gestor da própria unidade também pode editá-la.
    exigir_acesso_ong(db, usuario, ong_id, unidade_id, papeis=PAPEIS_GESTAO)
    try:
        return ong_service.atualizar_unidade(db, ong_id, unidade_id, dados)
    except (RecursoNaoEncontrado, ConflitoDeEstado) as exc:
        raise _erro_http(exc)


@router.delete("/{ong_id}/unidades/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_unidade(
    ong_id: uuid.UUID,
    unidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = _GESTOR,
):
    exigir_acesso_ong(db, usuario, ong_id, None, papeis=PAPEIS_GESTAO)
    try:
        ong_service.remover_unidade(db, ong_id, unidade_id)
    except (RecursoNaoEncontrado, ConflitoDeEstado) as exc:
        raise _erro_http(exc)
