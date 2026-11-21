"""Inscrições e presença (VAP REGISTER_ACTION / CANCEL_REGISTRATION; check-in/out via REST).

A lotação NÃO é validada aqui. O trigger trg_inscricao_valida faz
SELECT ... FOR UPDATE na ação e é a única barreira correta sob
concorrência. Estes serviços apenas traduzem o erro do banco.

Inscrição e cancelamento avisam os gestores da ONG (notificação gravada
na mesma transação; ver notificacao_service).
"""
import datetime as dt
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflitoDeEstado, RecursoNaoEncontrado
from app.models import (
    AcaoSocial,
    Inscricao,
    Ong,
    Presenca,
    StatusAcao,
    StatusInscricao,
    TipoNotificacao,
    Unidade,
    Usuario,
    Voluntario,
)
from app.services import notificacao_service

_ACAO_ENCERRADA = frozenset({StatusAcao.CONCLUIDA, StatusAcao.CANCELADA})


def _voluntario_do_usuario(db: Session, usuario_id: uuid.UUID) -> Voluntario:
    voluntario = db.scalar(select(Voluntario).where(Voluntario.usuario_id == usuario_id))
    if voluntario is None:
        raise RecursoNaoEncontrado("Usuário não possui perfil de voluntário")
    return voluntario


def _nome_do_usuario(db: Session, usuario_id: uuid.UUID) -> str:
    usuario = db.get(Usuario, usuario_id)
    return usuario.nome if usuario else "Um voluntário"


def _avisar_gestores_inscricao(db: Session, usuario_id: uuid.UUID, acao_id: uuid.UUID) -> None:
    acao = db.get(AcaoSocial, acao_id)
    if acao is None:
        return
    notificacao_service.notificar_gestores(
        db, acao, TipoNotificacao.INSCRICAO_CONFIRMADA, "Nova inscrição",
        f'{_nome_do_usuario(db, usuario_id)} se inscreveu em "{acao.titulo}".',
    )


def _traduzir_erro_inscricao(db: Session, exc: IntegrityError) -> Exception:
    """Desfaz a transação e traduz o erro dos triggers/constraints."""
    db.rollback()
    detalhe = str(exc.orig).lower()
    if "lotada" in detalhe:
        return ConflitoDeEstado("Ação social lotada")
    if "inscricao_uk" in detalhe:
        # Corrida: outra requisição inseriu entre o SELECT e o INSERT.
        return ConflitoDeEstado("Voluntário já inscrito nesta ação")
    if "status" in detalhe:
        return ConflitoDeEstado("Ação não aceita inscrições no status atual")
    if "foreign key" in detalhe or "não encontrada" in detalhe:
        return RecursoNaoEncontrado("Ação social não encontrada")
    return exc


def inscrever(db: Session, usuario_id: uuid.UUID, acao_id: uuid.UUID) -> Inscricao:
    voluntario = _voluntario_do_usuario(db, usuario_id)

    # A UNIQUE (acao_id, voluntario_id) vale também para inscrições
    # canceladas. Sem reativar a linha existente, quem cancelasse uma vez
    # ficaria impedido de voltar à mesma ação para sempre.
    existente = db.scalar(
        select(Inscricao).where(
            Inscricao.acao_id == acao_id,
            Inscricao.voluntario_id == voluntario.id,
        )
    )
    if existente is not None:
        if existente.status != StatusInscricao.CANCELADA:
            raise ConflitoDeEstado("Voluntário já inscrito nesta ação")
        # Reativa: status e cancelado_em mudam juntos por causa da
        # CHECK inscricao_cancelamento_chk.
        existente.status = StatusInscricao.CONFIRMADA
        existente.cancelado_em = None
        existente.motivo_cancelamento = None
        inscricao = existente
    else:
        inscricao = Inscricao(
            acao_id=acao_id,
            voluntario_id=voluntario.id,
            status=StatusInscricao.CONFIRMADA,
        )
        db.add(inscricao)

    # flush primeiro: o trigger de lotação roda aqui, antes de gastar
    # trabalho com a notificação de uma inscrição que vai falhar.
    try:
        db.flush()
        _avisar_gestores_inscricao(db, usuario_id, acao_id)
        db.commit()
    except IntegrityError as exc:
        raise _traduzir_erro_inscricao(db, exc) from exc
    db.refresh(inscricao)
    return inscricao


def cancelar(
    db: Session, usuario_id: uuid.UUID, acao_id: uuid.UUID, motivo: str | None = None
) -> Inscricao:
    voluntario = _voluntario_do_usuario(db, usuario_id)
    inscricao = db.scalar(
        select(Inscricao).where(
            Inscricao.acao_id == acao_id,
            Inscricao.voluntario_id == voluntario.id,
        )
    )
    if inscricao is None:
        raise RecursoNaoEncontrado("Inscrição não encontrada")
    if inscricao.status == StatusInscricao.CANCELADA:
        raise ConflitoDeEstado("Inscrição já estava cancelada")
    acao = db.get(AcaoSocial, acao_id)
    if acao is not None and StatusAcao(acao.status) in _ACAO_ENCERRADA:
        raise ConflitoDeEstado("Não é possível cancelar a participação numa ação encerrada")

    # status e cancelado_em precisam mudar juntos: a CHECK
    # inscricao_cancelamento_chk rejeita os dois em desacordo.
    inscricao.status = StatusInscricao.CANCELADA
    inscricao.cancelado_em = dt.datetime.now(dt.timezone.utc)
    inscricao.motivo_cancelamento = motivo
    if acao is not None:
        notificacao_service.notificar_gestores(
            db, acao, TipoNotificacao.INSCRICAO_CANCELADA, "Inscrição cancelada",
            f'{_nome_do_usuario(db, usuario_id)} cancelou a participação em "{acao.titulo}".',
        )
    db.commit()
    db.refresh(inscricao)
    return inscricao


def _hoje_local() -> dt.date:
    return dt.datetime.now(ZoneInfo(settings.fuso_horario)).date()


def check_in(db: Session, inscricao_id: uuid.UUID, registrado_por: uuid.UUID) -> Presenca:
    if db.get(Presenca, inscricao_id) is not None:
        raise ConflitoDeEstado("Check-in já registrado para esta inscrição")

    inscricao = db.get(Inscricao, inscricao_id)
    acao = db.get(AcaoSocial, inscricao.acao_id) if inscricao else None
    if acao is not None:
        if StatusAcao(acao.status) in (StatusAcao.CANCELADA, StatusAcao.RASCUNHO):
            raise ConflitoDeEstado("Ação cancelada ou não publicada não aceita presença")
        inicio_local = acao.inicio.astimezone(ZoneInfo(settings.fuso_horario)).date()
        if _hoje_local() < inicio_local:
            raise ConflitoDeEstado("A presença só pode ser registrada a partir do dia da ação")

    presenca = Presenca(
        inscricao_id=inscricao_id,
        check_in=dt.datetime.now(dt.timezone.utc),
        registrado_por=registrado_por,
    )
    db.add(presenca)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "inscrição confirmada" in str(exc.orig).lower():
            raise ConflitoDeEstado("Presença exige inscrição confirmada") from exc
        raise
    db.refresh(presenca)
    return presenca


def check_out(db: Session, inscricao_id: uuid.UUID) -> Presenca:
    presenca = db.get(Presenca, inscricao_id)
    if presenca is None:
        raise RecursoNaoEncontrado("Não há check-in para esta inscrição")
    if presenca.check_out is not None:
        raise ConflitoDeEstado("Check-out já registrado")

    presenca.check_out = dt.datetime.now(dt.timezone.utc)
    db.commit()
    # horas_computadas é GENERATED: só aparece após reler do banco.
    db.refresh(presenca)
    return presenca


# ---------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------

def listar_da_acao(
    db: Session, acao_id: uuid.UUID, *, incluir_canceladas: bool = False
) -> list[dict]:
    """Inscritos de uma ação com dados de contato e presença (uma consulta)."""
    consulta = (
        select(
            Inscricao.id.label("inscricao_id"),
            Inscricao.status,
            Inscricao.inscrito_em,
            Voluntario.id.label("voluntario_id"),
            Usuario.nome,
            Usuario.email,
            Voluntario.telefone,
            Presenca.check_in,
            Presenca.check_out,
            Presenca.horas_computadas,
        )
        .join(Voluntario, Voluntario.id == Inscricao.voluntario_id)
        .join(Usuario, Usuario.id == Voluntario.usuario_id)
        .outerjoin(Presenca, Presenca.inscricao_id == Inscricao.id)
        .where(Inscricao.acao_id == acao_id)
        .order_by(Usuario.nome, Inscricao.id)
    )
    if not incluir_canceladas:
        consulta = consulta.where(Inscricao.status != StatusInscricao.CANCELADA)
    return [dict(linha) for linha in db.execute(consulta).mappings().all()]


def listar_do_voluntario(
    db: Session, usuario_id: uuid.UUID, *, incluir_canceladas: bool = False
) -> list[dict]:
    """Inscrições do voluntário com o resumo da ação e a presença (uma consulta)."""
    consulta = (
        select(
            Inscricao.id, Inscricao.acao_id, Inscricao.voluntario_id, Inscricao.status,
            Inscricao.inscrito_em, Inscricao.cancelado_em,
            Presenca.check_in, Presenca.check_out, Presenca.horas_computadas,
            AcaoSocial.codigo, AcaoSocial.titulo, AcaoSocial.inicio, AcaoSocial.fim,
            AcaoSocial.status.label("acao_status"), AcaoSocial.causa, AcaoSocial.local_texto,
            AcaoSocial.ong_id, Ong.nome.label("ong_nome"),
            Unidade.cidade.label("unidade_cidade"), Unidade.uf.label("unidade_uf"),
        )
        .join(Voluntario, Voluntario.id == Inscricao.voluntario_id)
        .join(AcaoSocial, AcaoSocial.id == Inscricao.acao_id)
        .join(Ong, Ong.id == AcaoSocial.ong_id)
        .outerjoin(Unidade, Unidade.id == AcaoSocial.unidade_id)
        .outerjoin(Presenca, Presenca.inscricao_id == Inscricao.id)
        .where(Voluntario.usuario_id == usuario_id)
        .order_by(AcaoSocial.inicio.desc(), Inscricao.id)
    )
    if not incluir_canceladas:
        consulta = consulta.where(Inscricao.status != StatusInscricao.CANCELADA)
    resultado = []
    for linha in db.execute(consulta).mappings().all():
        resultado.append({
            "id": linha["id"], "acao_id": linha["acao_id"],
            "voluntario_id": linha["voluntario_id"], "status": linha["status"],
            "inscrito_em": linha["inscrito_em"], "cancelado_em": linha["cancelado_em"],
            "check_in": linha["check_in"], "check_out": linha["check_out"],
            "horas_computadas": linha["horas_computadas"],
            "acao": {
                "id": linha["acao_id"], "codigo": linha["codigo"],
                "titulo": linha["titulo"], "inicio": linha["inicio"], "fim": linha["fim"],
                "status": linha["acao_status"], "causa": linha["causa"],
                "local_texto": linha["local_texto"],
                "ong_id": linha["ong_id"], "ong_nome": linha["ong_nome"],
                "unidade_cidade": linha["unidade_cidade"], "unidade_uf": linha["unidade_uf"],
            },
        })
    return resultado
