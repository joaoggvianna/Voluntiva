"""Regras de negócio reais, substituindo o mock de protocol/services.py.

Cumpre o que docs/VAP.md seção 7 pede: VAP e REST chamam exatamente os
mesmos services de app/services. Nenhuma regra é reescrita aqui — este
módulo só traduz identificadores e exceções entre os dois mundos.

E cumpre a seção 8: a disputa pela última vaga é resolvida no PostgreSQL,
pelo trigger com SELECT ... FOR UPDATE, não por lock em memória do
servidor. Um lock de processo não protegeria nada, já que a API REST
escreve no mesmo banco por outro processo.

Ligado no boot por protocol/__main__.py, via handlers.set_services().
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.exceptions import (
    ConflitoDeEstado,
    DadosInvalidos,
    PermissaoNegada,
    RecursoNaoEncontrado,
    VoluntivaError,
)
from app.db.session import SessionLocal
from app.models import AcaoSocial, StatusAcao
from app.services import acao_service, inscricao_service

from .errors import BadRequest, Conflict, Forbidden, NotFound, VAPError

# Exceção de domínio -> erro do protocolo. Espelha o mapeamento HTTP
# de app/main.py, para os dois transportes concordarem.
_ERRO_VAP: dict[type[VoluntivaError], type[VAPError]] = {
    RecursoNaoEncontrado: NotFound,
    ConflitoDeEstado: Conflict,
    PermissaoNegada: Forbidden,
    DadosInvalidos: BadRequest,
}


def _traduzir(exc: VoluntivaError) -> VAPError:
    return _ERRO_VAP.get(type(exc), VAPError)(exc.mensagem)


# Vocabulário do protocolo é inglês (docs/VAP.md); o do banco é português.
# O mock original devolvia "OPEN", então mantemos esse vocabulário.
_STATUS_PROTOCOLO = {
    "rascunho": "DRAFT",
    "publicada": "OPEN",
    "em_andamento": "IN_PROGRESS",
    "concluida": "CLOSED",
    "cancelada": "CANCELLED",
}


def _acao_por_codigo(db, action_id: int) -> AcaoSocial:
    """Converte o inteiro público do protocolo no UUID interno.

    Ver db/migrations/0002 para o porquê de existirem dois identificadores.
    """
    acao = db.scalar(select(AcaoSocial).where(AcaoSocial.codigo == action_id))
    if acao is None:
        raise NotFound("Action not found")
    return acao


def list_actions() -> list[dict]:
    db = SessionLocal()
    try:
        linhas = acao_service.listar_com_vagas(db, status=StatusAcao.PUBLICADA, limite=100)
        # Devolve só o que o cliente precisa e no vocabulário do protocolo.
        # Nunca expõe o UUID interno nem ids de outras entidades.
        return [
            {
                "id": linha["codigo"],
                "title": linha["titulo"],
                "status": _STATUS_PROTOCOLO.get(linha["status"], "UNKNOWN"),
                "starts_at": linha["inicio"].isoformat(),
                "capacity": linha["vagas"],
                "available": linha["vagas_disponiveis"],
            }
            for linha in linhas
        ]
    finally:
        db.close()


def register_action(user_id: str, role: str, action_id: int) -> dict:
    if role != "VOLUNTEER":
        raise Forbidden("Only volunteers can register")

    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        try:
            inscricao_service.inscrever(db, uuid.UUID(user_id), acao.id)
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return {"action_id": action_id, "status": "REGISTERED"}
    finally:
        db.close()


def cancel_registration(user_id: str, role: str, action_id: int) -> dict:
    if role != "VOLUNTEER":
        raise Forbidden("Only volunteers can cancel registrations")

    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        try:
            inscricao_service.cancelar(db, uuid.UUID(user_id), acao.id)
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return {"action_id": action_id, "status": "CANCELLED"}
    finally:
        db.close()
