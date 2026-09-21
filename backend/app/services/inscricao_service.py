"""Inscrições e presença (JOIN_EVENT / LEAVE_EVENT / CHECK_IN / CHECK_OUT).

A lotação NÃO é validada aqui. O trigger trg_inscricao_valida faz
SELECT ... FOR UPDATE na ação e é a única barreira correta sob
concorrência. Estes serviços apenas traduzem o erro do banco.
"""
import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoDeEstado, RecursoNaoEncontrado
from app.models import Inscricao, Presenca, StatusInscricao, Voluntario


def _voluntario_do_usuario(db: Session, usuario_id: uuid.UUID) -> Voluntario:
    voluntario = db.scalar(select(Voluntario).where(Voluntario.usuario_id == usuario_id))
    if voluntario is None:
        raise RecursoNaoEncontrado("Usuário não possui perfil de voluntário")
    return voluntario


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
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            if "lotada" in str(exc.orig).lower():
                raise ConflitoDeEstado("Ação social lotada") from exc
            raise
        db.refresh(existente)
        return existente

    inscricao = Inscricao(
        acao_id=acao_id,
        voluntario_id=voluntario.id,
        status=StatusInscricao.CONFIRMADA,
    )
    db.add(inscricao)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        detalhe = str(exc.orig).lower()
        if "lotada" in detalhe:
            raise ConflitoDeEstado("Ação social lotada") from exc
        if "inscricao_uk" in detalhe:
            # Corrida: outra requisição inseriu entre o SELECT e o INSERT.
            raise ConflitoDeEstado("Voluntário já inscrito nesta ação") from exc
        if "status" in detalhe:
            raise ConflitoDeEstado("Ação não aceita inscrições no status atual") from exc
        raise
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

    # status e cancelado_em precisam mudar juntos: a CHECK
    # inscricao_cancelamento_chk rejeita os dois em desacordo.
    inscricao.status = StatusInscricao.CANCELADA
    inscricao.cancelado_em = dt.datetime.now(dt.timezone.utc)
    inscricao.motivo_cancelamento = motivo
    db.commit()
    db.refresh(inscricao)
    return inscricao


def check_in(db: Session, inscricao_id: uuid.UUID, registrado_por: uuid.UUID) -> Presenca:
    if db.get(Presenca, inscricao_id) is not None:
        raise ConflitoDeEstado("Check-in já registrado para esta inscrição")

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
