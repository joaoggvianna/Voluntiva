"""Consulta e manutenção de ações sociais (LIST_EVENTS / CREATE_EVENT / UPDATE_EVENT)."""
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNaoEncontrado
from app.models import AcaoHabilidade, AcaoSocial, StatusAcao
from app.schemas.acao import AcaoCreate, AcaoUpdate


def listar_com_vagas(
    db: Session,
    *,
    status: StatusAcao | None = StatusAcao.PUBLICADA,
    ong_id: uuid.UUID | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Lê a view vw_acao_vagas, que já calcula ocupação e lista de espera.

    Consulta parametrizada: os valores vão como bind params, nunca
    concatenados na string SQL.
    """
    sql = text("""
        SELECT acao_id, codigo, ong_id, ong_nome, unidade_id, titulo, inicio, fim,
               status, vagas, vagas_ocupadas, vagas_disponiveis, em_lista_espera
          FROM public.vw_acao_vagas
         WHERE (CAST(:status AS public.status_acao) IS NULL
                OR status = CAST(:status AS public.status_acao))
           AND (CAST(:ong_id AS uuid) IS NULL
                OR ong_id = CAST(:ong_id AS uuid))
         ORDER BY inicio
         LIMIT :limite OFFSET :offset
    """)
    linhas = db.execute(sql, {
        "status": status.value if status else None,
        "ong_id": ong_id,
        "limite": limite,
        "offset": offset,
    }).mappings().all()
    return [dict(linha) for linha in linhas]


def obter(db: Session, acao_id: uuid.UUID) -> AcaoSocial:
    acao = db.get(AcaoSocial, acao_id)
    if acao is None:
        raise RecursoNaoEncontrado("Ação social não encontrada")
    return acao


def criar(db: Session, dados: AcaoCreate, criado_por: uuid.UUID) -> AcaoSocial:
    acao = AcaoSocial(
        ong_id=dados.ong_id,
        unidade_id=dados.unidade_id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        local_texto=dados.local_texto,
        inicio=dados.inicio,
        fim=dados.fim,
        vagas=dados.vagas,
        criado_por=criado_por,
    )
    db.add(acao)
    db.flush()

    for habilidade_id in dados.habilidades:
        db.add(AcaoHabilidade(acao_id=acao.id, habilidade_id=habilidade_id))

    db.commit()
    db.refresh(acao)
    return acao


def atualizar(db: Session, acao_id: uuid.UUID, dados: AcaoUpdate) -> AcaoSocial:
    acao = obter(db, acao_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(acao, campo, valor)
    db.commit()
    db.refresh(acao)
    return acao


# TODO(equipe): filtro por habilidade e por disponibilidade do voluntário (RF004).
# A consulta precisa cruzar voluntario_habilidade com acao_habilidade e
# voluntario_disponibilidade com o dia da semana de acao_social.inicio.
