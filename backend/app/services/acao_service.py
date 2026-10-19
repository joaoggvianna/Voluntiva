"""Consulta e manutenção de ações sociais (LIST_EVENTS / CREATE_EVENT / UPDATE_EVENT)."""
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.exceptions import RecursoNaoEncontrado, PermissaoNegada, DadosInvalidos
from app.models import AcaoHabilidade, AcaoSocial, StatusAcao, TipoUsuario, OngMembro, Unidade
from app.schemas.acao import AcaoCreate, AcaoUpdate


def listar_com_vagas(
    db: Session,
    *,
    status: StatusAcao | None = StatusAcao.PUBLICADA,
    ong_id: uuid.UUID | None = None,
    limite: int = 50,
    offset: int = 0,
    voluntario_id: uuid.UUID | None = None,
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
           AND (CAST(:voluntario_id AS uuid) IS NULL OR (
              -- Toda habilidade obrigatória deve constar no perfil do voluntário.
              NOT EXISTS (
                SELECT 1 FROM public.acao_habilidade ah
                WHERE ah.acao_id = acao_id AND ah.obrigatoria
                  AND NOT EXISTS (
                    SELECT 1 FROM public.voluntario_habilidade vh
                    WHERE vh.voluntario_id = CAST(:voluntario_id AS uuid)
                      AND vh.habilidade_id = ah.habilidade_id
                  )
              )
              AND EXISTS (
                SELECT 1 FROM public.voluntario_disponibilidade vd
                WHERE vd.voluntario_id = CAST(:voluntario_id AS uuid)
                  AND vd.dia_semana = EXTRACT(DOW FROM inicio)::int
                  AND vd.hora_inicio <= inicio::time
                  AND vd.hora_fim >= fim::time
                  AND inicio::date = fim::date
              )
           ))
         ORDER BY inicio
         LIMIT :limite OFFSET :offset
    """)
    linhas = db.execute(sql, {
        "status": status.value if status else None,
        "ong_id": ong_id,
        "limite": limite,
        "offset": offset,
        "voluntario_id": voluntario_id,
    }).mappings().all()
    return [dict(linha) for linha in linhas]


def obter(db: Session, acao_id: uuid.UUID) -> AcaoSocial:
    acao = db.get(AcaoSocial, acao_id)
    if acao is None:
        raise RecursoNaoEncontrado("Ação social não encontrada")
    return acao


def exigir_gestao_ong(db: Session, usuario_id: uuid.UUID, tipo: TipoUsuario, ong_id: uuid.UUID, unidade_id: uuid.UUID | None = None) -> None:
    """Controla acesso por vínculo de ONG e, quando aplicável, de unidade."""
    if tipo == TipoUsuario.ADMIN:
        return
    if tipo != TipoUsuario.ONG:
        raise PermissaoNegada("Perfil sem permissão para gerir ações")
    vinculos = db.scalars(
        select(OngMembro).where(OngMembro.usuario_id == usuario_id, OngMembro.ong_id == ong_id)
    ).all()
    if not any(v.unidade_id is None or (unidade_id is not None and v.unidade_id == unidade_id) for v in vinculos):
        raise PermissaoNegada("Usuário não é gestor desta ONG/unidade")


def criar(db: Session, dados: AcaoCreate, criado_por: uuid.UUID, tipo: TipoUsuario | None = None) -> AcaoSocial:
    if tipo is not None:
        exigir_gestao_ong(db, criado_por, tipo, dados.ong_id, dados.unidade_id)
    if dados.unidade_id is not None:
        unidade = db.get(Unidade, dados.unidade_id)
        if unidade is None or unidade.ong_id != dados.ong_id:
            raise DadosInvalidos("Unidade não pertence à ONG informada")
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


def atualizar(db: Session, acao_id: uuid.UUID, dados: AcaoUpdate, *, usuario_id: uuid.UUID | None = None, tipo: TipoUsuario | None = None) -> AcaoSocial:
    acao = obter(db, acao_id)
    if usuario_id is not None and tipo is not None:
        exigir_gestao_ong(db, usuario_id, tipo, acao.ong_id, acao.unidade_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(acao, campo, valor)
    if acao.fim <= acao.inicio:
        raise DadosInvalidos('fim deve ser posterior a inicio')
    db.commit()
    db.refresh(acao)
    return acao
