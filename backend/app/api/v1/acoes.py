"""Rotas de ações sociais."""
import datetime as dt
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.autorizacao import (
    e_membro_da_ong,
    exigir_acesso_acao,
    exigir_acesso_ong,
    exigir_unidade_da_ong,
)
from app.api.deps import exigir_tipo, usuario_opcional
from app.core.exceptions import ConflitoDeEstado, DadosInvalidos, RecursoNaoEncontrado
from app.db.session import get_db
from app.models import CausaSocial, StatusAcao, TipoUsuario, Usuario, Voluntario
from app.realtime.entrega import agendar_entrega
from app.schemas.acao import AcaoComVagas, AcaoCreate, AcaoResponse, AcaoUpdate
from app.schemas.inscricao import InscritoResponse
from app.services import acao_service, inscricao_service

router = APIRouter(prefix="/acoes", tags=["ações sociais"])

# Status que qualquer pessoa vê. Rascunho é interno da ONG.
_STATUS_PUBLICOS = frozenset({
    StatusAcao.PUBLICADA, StatusAcao.EM_ANDAMENTO,
    StatusAcao.CONCLUIDA, StatusAcao.CANCELADA,
})


def _erro_http(exc: Exception) -> HTTPException:
    if isinstance(exc, RecursoNaoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, exc.mensagem)
    if isinstance(exc, ConflitoDeEstado):
        return HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, exc.mensagem)


@router.get("", response_model=list[AcaoComVagas])
def listar(
    response: Response,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_opcional),
    status_filtro: StatusAcao | None = Query(default=StatusAcao.PUBLICADA, alias="status"),
    todos_status: bool = Query(
        default=False, description="Ignora `status` (só para membros da ONG em `ong_id`)."
    ),
    ong_id: uuid.UUID | None = None,
    busca: str | None = Query(default=None, max_length=100),
    uf: str | None = Query(default=None, pattern=r"^[A-Z]{2}$"),
    causa: CausaSocial | None = None,
    de: dt.date | None = None,
    ate: dt.date | None = None,
    com_vagas: bool = False,
    futuras: bool = False,
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Lista ações com ocupação. O total sem paginação vai no cabeçalho
    `X-Total-Count`.

    Rascunhos (`status=rascunho` ou `todos_status=true`) só aparecem para
    membros da ONG indicada em `ong_id`.
    """
    filtro = None if todos_status else status_filtro
    if filtro not in _STATUS_PUBLICOS:
        if ong_id is None or not e_membro_da_ong(db, usuario, ong_id):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Rascunhos só podem ser listados por membros da ONG (informe ong_id)",
            )
    itens, total = acao_service.buscar(
        db, status=filtro, ong_id=ong_id, busca=busca, uf=uf, causa=causa, de=de, ate=ate,
        com_vagas=com_vagas, futuras=futuras, limite=limite, offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    return itens


@router.get("/compativeis", response_model=list[AcaoComVagas])
def listar_compativeis(
    response: Response,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.VOLUNTARIO)),
    limite: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """RF004: ações publicadas e futuras compatíveis com as habilidades e a
    disponibilidade do voluntário autenticado. Declarada antes de
    /{acao_id} para não ser capturada por ela."""
    voluntario = db.scalar(select(Voluntario).where(Voluntario.usuario_id == usuario.id))
    if voluntario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Perfil de voluntário não encontrado")
    itens, total = acao_service.buscar(
        db, voluntario_id=voluntario.id, futuras=True, limite=limite, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return itens


@router.get("/{acao_id}", response_model=AcaoComVagas)
def obter(
    acao_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario | None = Depends(usuario_opcional),
):
    try:
        acao = acao_service.obter_detalhe(db, acao_id)
    except RecursoNaoEncontrado as exc:
        raise _erro_http(exc)
    # Rascunho de outra ONG responde 404: nem confirma que existe.
    if acao["status"] not in _STATUS_PUBLICOS and not e_membro_da_ong(db, usuario, acao["ong_id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ação social não encontrada")
    return acao


@router.get("/{acao_id}/inscricoes", response_model=list[InscritoResponse])
def listar_inscritos(
    acao_id: uuid.UUID,
    incluir_canceladas: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN)),
):
    """Inscritos da ação, com presença. Só para quem gere a ação."""
    try:
        acao = acao_service.obter(db, acao_id)
    except RecursoNaoEncontrado as exc:
        raise _erro_http(exc)
    exigir_acesso_acao(db, usuario, acao)
    return inscricao_service.listar_da_acao(db, acao_id, incluir_canceladas=incluir_canceladas)


@router.post("", response_model=AcaoResponse, status_code=status.HTTP_201_CREATED)
def criar(
    dados: AcaoCreate,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN)),
):
    exigir_acesso_ong(db, usuario, dados.ong_id, dados.unidade_id)
    exigir_unidade_da_ong(db, dados.ong_id, dados.unidade_id)
    try:
        acao = acao_service.criar(db, dados, criado_por=usuario.id)
    except (DadosInvalidos, ConflitoDeEstado) as exc:
        raise _erro_http(exc)
    agendar_entrega(db, tarefas)
    return acao


@router.patch("/{acao_id}", response_model=AcaoResponse)
def atualizar(
    acao_id: uuid.UUID,
    dados: AcaoUpdate,
    tarefas: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(exigir_tipo(TipoUsuario.ONG, TipoUsuario.ADMIN)),
):
    try:
        acao = acao_service.obter(db, acao_id)
        exigir_acesso_acao(db, usuario, acao)
        if "unidade_id" in dados.model_fields_set:
            # Mudar de unidade exige acesso também à unidade de destino.
            exigir_acesso_ong(db, usuario, acao.ong_id, dados.unidade_id)
            exigir_unidade_da_ong(db, acao.ong_id, dados.unidade_id)
        acao = acao_service.atualizar(db, acao_id, dados)
    except (RecursoNaoEncontrado, ConflitoDeEstado, DadosInvalidos) as exc:
        raise _erro_http(exc)
    agendar_entrega(db, tarefas)
    return acao
