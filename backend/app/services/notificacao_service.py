"""Notificações: gravação em lote, consulta e leitura.

Gravação
    Cada função `notificar_*` faz um único INSERT ... SELECT ... RETURNING
    na MESMA transação da mudança que a originou (cancelar ação, nova
    inscrição...). Se a mudança falhar, a notificação some junto; se der
    certo, as duas ficam gravadas.

Entrega em tempo real
    As linhas gravadas são guardadas em `db.info[PENDENTES]`. Depois do
    commit, a rota HTTP as envia pelo WebSocket (app/realtime/entrega.py),
    fora da transação. O servidor VAP grava as mesmas notificações, mas não
    tem WebSocket: o cliente as lê depois pela API.
"""
import datetime as dt
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import RecursoNaoEncontrado
from app.models import AcaoSocial, Notificacao, TipoNotificacao
from app.services.compatibilidade import condicao_compativel

PENDENTES = "notificacoes_pendentes"

_RETORNO = "RETURNING id, usuario_id, acao_id, tipo, titulo, mensagem, lida, criada_em"


def formatar_quando(instante: dt.datetime) -> str:
    local = instante.astimezone(ZoneInfo(settings.fuso_horario))
    return local.strftime("%d/%m/%Y às %H:%M")


def _gravar(db: Session, sql: str, params: dict) -> list[dict]:
    linhas = [dict(linha) for linha in db.execute(text(sql), params).mappings().all()]
    db.info.setdefault(PENDENTES, []).extend(linhas)
    return linhas


def _params(acao: AcaoSocial, tipo: TipoNotificacao, titulo: str, mensagem: str) -> dict:
    return {
        "acao_id": acao.id,
        "tipo": tipo.value,
        "titulo": titulo[:160],
        "mensagem": mensagem[:2000],
    }


def notificar_inscritos(
    db: Session, acao: AcaoSocial, tipo: TipoNotificacao, titulo: str, mensagem: str
) -> list[dict]:
    """Voluntários com inscrição confirmada na ação."""
    return _gravar(db, f"""
        INSERT INTO public.notificacao (usuario_id, acao_id, tipo, titulo, mensagem)
        SELECT v.usuario_id, i.acao_id, CAST(:tipo AS public.tipo_notificacao), :titulo, :mensagem
          FROM public.inscricao i
          JOIN public.voluntario v ON v.id = i.voluntario_id
         WHERE i.acao_id = :acao_id
           AND i.status = 'confirmada'
        {_RETORNO}
    """, _params(acao, tipo, titulo, mensagem))


def notificar_gestores(
    db: Session, acao: AcaoSocial, tipo: TipoNotificacao, titulo: str, mensagem: str
) -> list[dict]:
    """Membros da ONG com acesso à ação (ONG inteira ou a unidade da ação)."""
    return _gravar(db, f"""
        INSERT INTO public.notificacao (usuario_id, acao_id, tipo, titulo, mensagem)
        SELECT DISTINCT m.usuario_id, CAST(:acao_id AS uuid),
               CAST(:tipo AS public.tipo_notificacao), :titulo, :mensagem
          FROM public.ong_membro m
          JOIN public.usuario u ON u.id = m.usuario_id AND u.ativo
         WHERE m.ong_id = :ong_id
           AND (m.unidade_id IS NULL
                OR m.unidade_id = CAST(:unidade_id AS uuid))
        {_RETORNO}
    """, {
        **_params(acao, tipo, titulo, mensagem),
        "ong_id": acao.ong_id,
        "unidade_id": acao.unidade_id,
    })


def notificar_compativeis(db: Session, acao: AcaoSocial, nome_ong: str) -> list[dict]:
    """Nova ação publicada: avisa os voluntários compatíveis (RF004)."""
    condicao = condicao_compativel(
        acao_id="a.id", inicio="a.inicio", fim="a.fim", voluntario_id="v.id"
    )
    return _gravar(db, f"""
        INSERT INTO public.notificacao (usuario_id, acao_id, tipo, titulo, mensagem)
        SELECT v.usuario_id, a.id, CAST(:tipo AS public.tipo_notificacao), :titulo, :mensagem
          FROM public.acao_social a
          CROSS JOIN public.voluntario v
          JOIN public.usuario u ON u.id = v.usuario_id AND u.ativo
         WHERE a.id = :acao_id
           AND {condicao}
        {_RETORNO}
    """, {
        **_params(
            acao,
            TipoNotificacao.ACAO_CRIADA,
            "Nova ação com a sua cara",
            f'{nome_ong} publicou a ação "{acao.titulo}" para {formatar_quando(acao.inicio)}.',
        ),
        "fuso": settings.fuso_horario,
    })


# ---------------------------------------------------------------------
# Consulta
# ---------------------------------------------------------------------

def listar(
    db: Session,
    usuario_id: uuid.UUID,
    *,
    apenas_nao_lidas: bool = False,
    limite: int = 50,
    offset: int = 0,
) -> list[Notificacao]:
    consulta = select(Notificacao).where(Notificacao.usuario_id == usuario_id)
    if apenas_nao_lidas:
        consulta = consulta.where(Notificacao.lida.is_(False))
    return list(db.scalars(
        consulta.order_by(Notificacao.criada_em.desc(), Notificacao.id)
        .limit(limite).offset(offset)
    ).all())


def contar_nao_lidas(db: Session, usuario_id: uuid.UUID) -> int:
    # Usa o índice parcial notificacao_nao_lidas_idx.
    return db.scalar(
        select(func.count()).select_from(Notificacao).where(
            Notificacao.usuario_id == usuario_id, Notificacao.lida.is_(False)
        )
    ) or 0


def marcar_lida(db: Session, usuario_id: uuid.UUID, notificacao_id: uuid.UUID) -> Notificacao:
    notificacao = db.get(Notificacao, notificacao_id)
    # Notificação de outra pessoa responde 404, não 403: não confirma que o id existe.
    if notificacao is None or notificacao.usuario_id != usuario_id:
        raise RecursoNaoEncontrado("Notificação não encontrada")
    if not notificacao.lida:
        notificacao.lida = True
        db.commit()
        db.refresh(notificacao)
    return notificacao


def marcar_todas_lidas(db: Session, usuario_id: uuid.UUID) -> int:
    resultado = db.execute(
        update(Notificacao)
        .where(Notificacao.usuario_id == usuario_id, Notificacao.lida.is_(False))
        .values(lida=True)
    )
    db.commit()
    return resultado.rowcount or 0
