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

import datetime as dt
import uuid

from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.exceptions import (
    ConflitoDeEstado,
    DadosInvalidos,
    PermissaoNegada,
    RecursoNaoEncontrado,
    VoluntivaError,
)
from app.db.session import SessionLocal
from app.models import (
    AcaoSocial,
    Inscricao,
    OngMembro,
    StatusAcao,
    StatusInscricao,
    TipoUsuario,
    Unidade,
    Usuario,
    Voluntario,
)
from app.schemas.acao import AcaoCreate, AcaoUpdate
from app.services import acao_service, inscricao_service, notificacao_service, permissao

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


def register_action(user_id: str, role: str, action_id: int, *, waitlist: bool = False) -> dict:
    if role != "VOLUNTEER":
        raise Forbidden("Only volunteers can register")

    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        try:
            inscricao = inscricao_service.inscrever(
                db, uuid.UUID(user_id), acao.id, lista_espera=waitlist
            )
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        em_espera = inscricao.status == StatusInscricao.LISTA_ESPERA
        return {"action_id": action_id, "status": "WAITLISTED" if em_espera else "REGISTERED"}
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


# ---------------------------------------------------------------------
# Gestão de ações, presença e notificações
#
# Mesmo princípio dos comandos acima: validação de negócio e autorização
# vêm de app/services (acao_service, inscricao_service, permissao); aqui
# só há tradução de vocabulário (inglês do protocolo <-> português do
# banco) e de identificadores (codigo inteiro <-> UUID).
#
# Limitação: notificações geradas por comandos VAP são gravadas no banco,
# mas o push em tempo real (WebSocket) só existe no processo da API.
# A interface web as recebe na próxima carga; clientes VAP usam
# LIST_NOTIFICATIONS.
# ---------------------------------------------------------------------

_STATUS_BANCO = {v: k for k, v in _STATUS_PROTOCOLO.items()}

_TIPO_POR_PAPEL = {"ONG": TipoUsuario.ONG, "ADMIN": TipoUsuario.ADMIN}

# Campo do protocolo -> campo dos schemas de ação.
_CAMPOS = {
    "title": "titulo",
    "description": "descricao",
    "location": "local_texto",
    "starts_at": "inicio",
    "ends_at": "fim",
    "capacity": "vagas",
    "unit_id": "unidade_id",
}


def _uuid(valor: str, campo: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (ValueError, TypeError) as exc:
        raise BadRequest(f"{campo} must be a UUID") from exc


def _instante(valor: str, campo: str) -> dt.datetime:
    try:
        instante = dt.datetime.fromisoformat(valor)
    except ValueError as exc:
        raise BadRequest(f"{campo} must be an ISO 8601 datetime") from exc
    if instante.tzinfo is None:
        raise BadRequest(f"{campo} must include a timezone offset")
    return instante


def _traduzir_campos(campos: dict) -> dict:
    dados = {}
    for nome, valor in campos.items():
        if nome in ("starts_at", "ends_at"):
            valor = _instante(valor, nome)
        elif nome == "unit_id":
            valor = _uuid(valor, nome)
        if nome in _CAMPOS:
            dados[_CAMPOS[nome]] = valor
    return dados


def _schema(classe, dados: dict):
    try:
        return classe(**dados)
    except ValidationError as exc:
        mensagem = str(exc.errors()[0].get("msg", "Invalid payload"))
        raise BadRequest(mensagem.removeprefix("Value error, ")) from exc


def _exigir_acesso(db, user_id: str, role: str, ong_id, unidade_id) -> None:
    tipo = _TIPO_POR_PAPEL.get(role)
    if tipo is None or not permissao.tem_acesso_ong(db, uuid.UUID(user_id), tipo, ong_id, unidade_id):
        raise Forbidden("Not a member of this organization or unit")


def _exigir_unidade(db, ong_id, unidade_id) -> None:
    if unidade_id is None:
        return
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.ong_id != ong_id or not unidade.ativo:
        raise BadRequest("unit_id does not belong to this organization")


def _ong_do_usuario(db, user_id: str) -> uuid.UUID:
    """Sem org_id, usa a ONG do usuário quando ele gere exatamente uma."""
    ongs = set(db.scalars(
        select(OngMembro.ong_id).where(OngMembro.usuario_id == uuid.UUID(user_id))
    ).all())
    if len(ongs) != 1:
        raise BadRequest("org_id is required")
    return ongs.pop()


def _acao_resposta(acao: AcaoSocial) -> dict:
    return {
        "id": acao.codigo,
        "title": acao.titulo,
        "status": _STATUS_PROTOCOLO.get(StatusAcao(acao.status).value, "UNKNOWN"),
        "starts_at": acao.inicio.isoformat(),
        "ends_at": acao.fim.isoformat(),
        "capacity": acao.vagas,
    }


def create_action(user_id: str, role: str, campos: dict) -> dict:
    db = SessionLocal()
    try:
        if "org_id" in campos:
            ong_id = _uuid(campos["org_id"], "org_id")
        elif role == "ADMIN":
            raise BadRequest("org_id is required")
        else:
            ong_id = _ong_do_usuario(db, user_id)
        dados = _traduzir_campos(campos)
        dados["habilidades"] = [_uuid(s, "skills") for s in campos.get("skills", [])]
        dados["status"] = StatusAcao.PUBLICADA if campos.get("publish") else StatusAcao.RASCUNHO
        novo = _schema(AcaoCreate, {"ong_id": ong_id, **dados})
        _exigir_acesso(db, user_id, role, novo.ong_id, novo.unidade_id)
        _exigir_unidade(db, novo.ong_id, novo.unidade_id)
        try:
            acao = acao_service.criar(db, novo, criado_por=uuid.UUID(user_id))
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return _acao_resposta(acao)
    finally:
        db.close()


def update_action(user_id: str, role: str, action_id: int, campos: dict) -> dict:
    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        _exigir_acesso(db, user_id, role, acao.ong_id, acao.unidade_id)
        dados = _traduzir_campos(campos)
        if "status" in campos:
            dados["status"] = StatusAcao(_STATUS_BANCO[campos["status"]])
        if "unidade_id" in dados:
            _exigir_acesso(db, user_id, role, acao.ong_id, dados["unidade_id"])
            _exigir_unidade(db, acao.ong_id, dados["unidade_id"])
        mudancas = _schema(AcaoUpdate, dados)
        try:
            acao = acao_service.atualizar(db, acao.id, mudancas)
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return _acao_resposta(acao)
    finally:
        db.close()


def _inscricao_por_email(db, acao: AcaoSocial, email: str) -> Inscricao:
    inscricao = db.scalar(
        select(Inscricao)
        .join(Voluntario, Voluntario.id == Inscricao.voluntario_id)
        .join(Usuario, Usuario.id == Voluntario.usuario_id)
        .where(Inscricao.acao_id == acao.id, func.lower(Usuario.email) == email.lower())
    )
    if inscricao is None:
        raise NotFound("Registration not found")
    return inscricao


def _presenca_resposta(action_id: int, email: str, presenca) -> dict:
    horas = presenca.horas_computadas
    return {
        "action_id": action_id,
        "volunteer_email": email,
        "check_in": presenca.check_in.isoformat(),
        "check_out": presenca.check_out.isoformat() if presenca.check_out else None,
        "hours": float(horas) if horas is not None else None,
    }


def check_in(user_id: str, role: str, action_id: int, email: str) -> dict:
    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        _exigir_acesso(db, user_id, role, acao.ong_id, acao.unidade_id)
        inscricao = _inscricao_por_email(db, acao, email)
        try:
            presenca = inscricao_service.check_in(
                db, inscricao.id, registrado_por=uuid.UUID(user_id)
            )
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return _presenca_resposta(action_id, email, presenca)
    finally:
        db.close()


def check_out(user_id: str, role: str, action_id: int, email: str) -> dict:
    db = SessionLocal()
    try:
        acao = _acao_por_codigo(db, action_id)
        _exigir_acesso(db, user_id, role, acao.ong_id, acao.unidade_id)
        inscricao = _inscricao_por_email(db, acao, email)
        try:
            presenca = inscricao_service.check_out(db, inscricao.id)
        except VoluntivaError as exc:
            raise _traduzir(exc) from exc
        return _presenca_resposta(action_id, email, presenca)
    finally:
        db.close()


def list_notifications(user_id: str, *, unread_only: bool = False, limit: int = 20) -> dict:
    db = SessionLocal()
    try:
        usuario_id = uuid.UUID(user_id)
        lista = notificacao_service.listar(
            db, usuario_id, apenas_nao_lidas=unread_only, limite=limit
        )
        acao_ids = {n.acao_id for n in lista if n.acao_id}
        codigos = dict(db.execute(
            select(AcaoSocial.id, AcaoSocial.codigo).where(AcaoSocial.id.in_(acao_ids))
        ).all()) if acao_ids else {}
        return {
            "unread": notificacao_service.contar_nao_lidas(db, usuario_id),
            "notifications": [
                {
                    "id": str(n.id),
                    "type": str(getattr(n.tipo, "value", n.tipo)).upper(),
                    "title": n.titulo,
                    "message": n.mensagem,
                    "read": n.lida,
                    "created_at": n.criada_em.isoformat(),
                    "action_id": codigos.get(n.acao_id),
                }
                for n in lista
            ],
        }
    finally:
        db.close()
