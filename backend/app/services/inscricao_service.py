"""Inscrições e presença (VAP REGISTER_ACTION / CANCEL_REGISTRATION; check-in/out via REST).

A lotação NÃO é validada aqui. O trigger trg_inscricao_valida faz
SELECT ... FOR UPDATE na ação e é a única barreira correta sob
concorrência. Estes serviços apenas traduzem o erro do banco.

Inscrição e cancelamento avisam os gestores da ONG (notificação gravada
na mesma transação; ver notificacao_service).

Lista de espera: com `lista_espera=True`, quem chega numa ação lotada
entra na fila (status lista_espera). Quando uma vaga confirmada é
cancelada, ou a ONG aumenta as vagas, os primeiros da fila são
confirmados na mesma transação e avisados.
"""
import datetime as dt
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
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
_ACAO_ACEITA_INSCRICAO = frozenset({StatusAcao.PUBLICADA, StatusAcao.EM_ANDAMENTO})


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


def contar_confirmadas(db: Session, acao_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(Inscricao).where(
            Inscricao.acao_id == acao_id,
            Inscricao.status == StatusInscricao.CONFIRMADA,
        )
    ) or 0


def _acao_aberta_para_inscricao(db: Session, acao_id: uuid.UUID) -> AcaoSocial:
    """Trava a linha da ação (a mesma que o trigger de lotação trava):
    contagem de vagas, lista de espera e promoção ficam serializadas."""
    acao = db.get(AcaoSocial, acao_id, with_for_update=True)
    if acao is None:
        raise RecursoNaoEncontrado("Ação social não encontrada")
    if StatusAcao(acao.status) not in _ACAO_ACEITA_INSCRICAO:
        raise ConflitoDeEstado("Ação não aceita inscrições no status atual")
    if acao.fim < dt.datetime.now(dt.timezone.utc):
        raise ConflitoDeEstado("Esta ação já foi realizada")
    return acao


def inscrever(
    db: Session, usuario_id: uuid.UUID, acao_id: uuid.UUID, *, lista_espera: bool = False
) -> Inscricao:
    """Inscreve com vaga confirmada. Ação lotada: sem `lista_espera`, recusa
    (409 "lotada"); com `lista_espera=True`, entra na fila por ordem de
    chegada e é promovido quando uma vaga abrir."""
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
    if existente is not None and existente.status != StatusInscricao.CANCELADA:
        if existente.status == StatusInscricao.LISTA_ESPERA:
            raise ConflitoDeEstado("Voluntário já está na lista de espera desta ação")
        raise ConflitoDeEstado("Voluntário já inscrito nesta ação")

    acao = _acao_aberta_para_inscricao(db, acao_id)
    status = StatusInscricao.CONFIRMADA
    if lista_espera and contar_confirmadas(db, acao_id) >= acao.vagas:
        status = StatusInscricao.LISTA_ESPERA

    if existente is not None:
        # Reativa: status e cancelado_em mudam juntos por causa da
        # CHECK inscricao_cancelamento_chk. A posição na fila recomeça.
        existente.status = status
        existente.cancelado_em = None
        existente.motivo_cancelamento = None
        existente.inscrito_em = dt.datetime.now(dt.timezone.utc)
        inscricao = existente
    else:
        inscricao = Inscricao(acao_id=acao_id, voluntario_id=voluntario.id, status=status)
        db.add(inscricao)

    # flush primeiro: o trigger de lotação roda aqui, antes de gastar
    # trabalho com a notificação de uma inscrição que vai falhar.
    try:
        db.flush()
        nome = _nome_do_usuario(db, usuario_id)
        if status == StatusInscricao.LISTA_ESPERA:
            notificacao_service.notificar_gestores(
                db, acao, TipoNotificacao.INSCRICAO_CONFIRMADA, "Nova pessoa na lista de espera",
                f'{nome} entrou na lista de espera de "{acao.titulo}".',
            )
        else:
            notificacao_service.notificar_gestores(
                db, acao, TipoNotificacao.INSCRICAO_CONFIRMADA, "Nova inscrição",
                f'{nome} se inscreveu em "{acao.titulo}".',
            )
        db.commit()
    except IntegrityError as exc:
        raise _traduzir_erro_inscricao(db, exc) from exc
    db.refresh(inscricao)
    return inscricao


def promover_lista_espera(db: Session, acao: AcaoSocial) -> list[Inscricao]:
    """Confirma os primeiros da fila até preencher as vagas livres.

    Quem chama precisa ter travado a linha da ação (FOR UPDATE) e feito
    flush da mudança que liberou a vaga. Não faz commit: a promoção entra
    na mesma transação do cancelamento ou do aumento de vagas.
    """
    livres = acao.vagas - contar_confirmadas(db, acao.id)
    if livres <= 0:
        return []
    fila = list(db.scalars(
        select(Inscricao)
        .where(Inscricao.acao_id == acao.id, Inscricao.status == StatusInscricao.LISTA_ESPERA)
        .order_by(Inscricao.inscrito_em, Inscricao.id)
        .limit(livres)
    ).all())
    if not fila:
        return []
    for inscricao in fila:
        inscricao.status = StatusInscricao.CONFIRMADA
    db.flush()
    usuarios = dict(db.execute(
        select(Voluntario.id, Voluntario.usuario_id)
        .where(Voluntario.id.in_([i.voluntario_id for i in fila]))
    ).all())
    for inscricao in fila:
        notificacao_service.notificar_usuario(
            db, usuarios[inscricao.voluntario_id], acao, TipoNotificacao.INSCRICAO_CONFIRMADA,
            "Sua vaga foi confirmada",
            f'Abriu uma vaga em "{acao.titulo}" e você saiu da lista de espera. '
            f"Te esperamos em {notificacao_service.formatar_quando(acao.inicio)}!",
        )
    return fila


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
    # FOR UPDATE: a promoção da fila disputa a mesma linha que inscrições
    # concorrentes; sem a trava, a vaga liberada poderia ir para duas pessoas.
    acao = db.get(AcaoSocial, acao_id, with_for_update=True)
    if acao is not None and StatusAcao(acao.status) in _ACAO_ENCERRADA:
        raise ConflitoDeEstado("Não é possível cancelar a participação numa ação encerrada")

    liberou_vaga = inscricao.status == StatusInscricao.CONFIRMADA
    # status e cancelado_em precisam mudar juntos: a CHECK
    # inscricao_cancelamento_chk rejeita os dois em desacordo.
    inscricao.status = StatusInscricao.CANCELADA
    inscricao.cancelado_em = dt.datetime.now(dt.timezone.utc)
    inscricao.motivo_cancelamento = motivo
    db.flush()
    if acao is not None:
        notificacao_service.notificar_gestores(
            db, acao, TipoNotificacao.INSCRICAO_CANCELADA, "Inscrição cancelada",
            f'{_nome_do_usuario(db, usuario_id)} cancelou a participação em "{acao.titulo}".',
        )
        if liberou_vaga:
            promover_lista_espera(db, acao)
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
