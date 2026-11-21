"""Consulta e manutenção de ações sociais (REST /acoes e VAP LIST_ACTIONS).

A autorização (quem pode criar/editar ação de qual ONG) fica em
app/api/autorizacao.py. Aqui ficam só as regras de negócio da ação,
para servirem igualmente à API REST e ao servidor VAP.
"""
import datetime as dt
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflitoDeEstado, DadosInvalidos, RecursoNaoEncontrado
from app.models import (
    AcaoHabilidade,
    AcaoSocial,
    Habilidade,
    Inscricao,
    Ong,
    StatusAcao,
    StatusInscricao,
    TipoNotificacao,
)
from app.schemas.acao import AcaoCreate, AcaoUpdate
from app.services import notificacao_service
from app.services.compatibilidade import condicao_compativel

# Máquina de estados da ação. Mudar para o mesmo status é sempre permitido
# (PATCH idempotente). concluida e cancelada são estados finais.
TRANSICOES_STATUS: dict[StatusAcao, frozenset[StatusAcao]] = {
    StatusAcao.RASCUNHO: frozenset({StatusAcao.PUBLICADA, StatusAcao.CANCELADA}),
    StatusAcao.PUBLICADA: frozenset(
        {StatusAcao.EM_ANDAMENTO, StatusAcao.CONCLUIDA, StatusAcao.CANCELADA}
    ),
    StatusAcao.EM_ANDAMENTO: frozenset({StatusAcao.CONCLUIDA, StatusAcao.CANCELADA}),
    StatusAcao.CONCLUIDA: frozenset(),
    StatusAcao.CANCELADA: frozenset(),
}

_ESTADOS_FINAIS = frozenset({StatusAcao.CONCLUIDA, StatusAcao.CANCELADA})

# Colunas NOT NULL: None no PATCH significa "não mexer".
_NAO_NULOS = frozenset({"titulo", "inicio", "fim", "vagas", "status"})


def _like(busca: str) -> str:
    """Escapa curingas do LIKE para a busca ser literal."""
    escapado = busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


_SQL_BUSCA = """
    SELECT v.acao_id, v.codigo, v.ong_id, v.ong_nome, v.unidade_id, v.titulo,
           v.inicio, v.fim, v.status, v.vagas, v.vagas_ocupadas,
           v.vagas_disponiveis, v.em_lista_espera,
           a.descricao, a.local_texto,
           un.nome   AS unidade_nome,
           un.cidade AS unidade_cidade,
           un.uf     AS unidade_uf,
           COALESCE((
               SELECT json_agg(json_build_object(
                          'id', h.id, 'nome', h.nome, 'obrigatoria', ah.obrigatoria)
                        ORDER BY h.nome)
                 FROM public.acao_habilidade ah
                 JOIN public.habilidade h ON h.id = ah.habilidade_id
                WHERE ah.acao_id = v.acao_id
           ), '[]'::json) AS habilidades,
           COUNT(*) OVER () AS total
      FROM public.vw_acao_vagas v
      JOIN public.acao_social a ON a.id = v.acao_id
      LEFT JOIN public.unidade un ON un.id = v.unidade_id
     WHERE (CAST(:status AS public.status_acao) IS NULL
            OR v.status = CAST(:status AS public.status_acao))
       AND (CAST(:ong_id AS uuid) IS NULL OR v.ong_id = CAST(:ong_id AS uuid))
       AND (CAST(:acao_id AS uuid) IS NULL OR v.acao_id = CAST(:acao_id AS uuid))
       AND (CAST(:busca AS text) IS NULL
            OR v.titulo ILIKE CAST(:busca AS text) ESCAPE '\\'
            OR a.descricao ILIKE CAST(:busca AS text) ESCAPE '\\'
            OR v.ong_nome ILIKE CAST(:busca AS text) ESCAPE '\\'
            OR un.cidade ILIKE CAST(:busca AS text) ESCAPE '\\')
       AND (CAST(:uf AS text) IS NULL OR un.uf = CAST(:uf AS text))
       AND (CAST(:de AS date) IS NULL
            OR (v.inicio AT TIME ZONE :fuso)::date >= CAST(:de AS date))
       AND (CAST(:ate AS date) IS NULL
            OR (v.inicio AT TIME ZONE :fuso)::date <= CAST(:ate AS date))
       AND (NOT CAST(:com_vagas AS boolean) OR v.vagas_disponiveis > 0)
       AND (NOT CAST(:futuras AS boolean) OR v.fim >= now())
       AND (CAST(:voluntario_id AS uuid) IS NULL OR {compativel})
     ORDER BY v.inicio, v.acao_id
     LIMIT :limite OFFSET :offset
""".format(compativel=condicao_compativel(
    acao_id="v.acao_id", inicio="v.inicio", fim="v.fim",
    voluntario_id="CAST(:voluntario_id AS uuid)",
))


def buscar(
    db: Session,
    *,
    status: StatusAcao | None = StatusAcao.PUBLICADA,
    ong_id: uuid.UUID | None = None,
    acao_id: uuid.UUID | None = None,
    voluntario_id: uuid.UUID | None = None,
    busca: str | None = None,
    uf: str | None = None,
    de: dt.date | None = None,
    ate: dt.date | None = None,
    com_vagas: bool = False,
    futuras: bool = False,
    limite: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Busca ações com ocupação (view vw_acao_vagas) e filtros.

    Devolve (itens, total), onde total é a contagem sem LIMIT/OFFSET,
    calculada na mesma consulta (COUNT(*) OVER ()).

    Com `voluntario_id`, aplica o filtro de compatibilidade (RF004), ver
    app/services/compatibilidade.py.

    Consulta parametrizada: os valores vão como bind params, nunca
    concatenados na string SQL.
    """
    busca = (busca or "").strip() or None
    linhas = db.execute(text(_SQL_BUSCA), {
        "status": status.value if status else None,
        "ong_id": ong_id,
        "acao_id": acao_id,
        "voluntario_id": voluntario_id,
        "busca": _like(busca) if busca else None,
        "uf": uf,
        "de": de,
        "ate": ate,
        "com_vagas": com_vagas,
        "futuras": futuras,
        "fuso": settings.fuso_horario,
        "limite": limite,
        "offset": offset,
    }).mappings().all()
    itens = [dict(linha) for linha in linhas]
    total = itens[0]["total"] if itens else 0
    for item in itens:
        del item["total"]
    return itens, total


def listar_com_vagas(
    db: Session,
    *,
    status: StatusAcao | None = StatusAcao.PUBLICADA,
    ong_id: uuid.UUID | None = None,
    limite: int = 50,
    offset: int = 0,
    voluntario_id: uuid.UUID | None = None,
) -> list[dict]:
    """Atalho usado pelo VAP (LIST_ACTIONS): só a lista, sem o total."""
    itens, _ = buscar(
        db, status=status, ong_id=ong_id, voluntario_id=voluntario_id,
        limite=limite, offset=offset,
    )
    return itens


def obter_detalhe(db: Session, acao_id: uuid.UUID) -> dict:
    itens, _ = buscar(db, status=None, acao_id=acao_id, limite=1)
    if not itens:
        raise RecursoNaoEncontrado("Ação social não encontrada")
    return itens[0]


def obter(db: Session, acao_id: uuid.UUID, *, para_atualizar: bool = False) -> AcaoSocial:
    acao = db.get(AcaoSocial, acao_id, with_for_update=para_atualizar)
    if acao is None:
        raise RecursoNaoEncontrado("Ação social não encontrada")
    return acao


def _validar_habilidades(db: Session, ids: set[uuid.UUID]) -> None:
    if not ids:
        return
    existentes = db.scalar(
        select(func.count()).select_from(Habilidade).where(Habilidade.id.in_(ids))
    )
    if existentes != len(ids):
        raise DadosInvalidos("Habilidade inexistente na lista informada")


def _nao_no_passado(inicio: dt.datetime) -> None:
    if inicio < dt.datetime.now(dt.timezone.utc):
        raise DadosInvalidos("A ação não pode começar no passado")


def _nome_ong(db: Session, ong_id: uuid.UUID) -> str:
    ong = db.get(Ong, ong_id)
    return ong.nome if ong else "Uma ONG"


def criar(db: Session, dados: AcaoCreate, criado_por: uuid.UUID) -> AcaoSocial:
    _nao_no_passado(dados.inicio)
    habilidades = set(dados.habilidades) | set(dados.habilidades_obrigatorias)
    _validar_habilidades(db, habilidades)

    acao = AcaoSocial(
        ong_id=dados.ong_id,
        unidade_id=dados.unidade_id,
        titulo=dados.titulo,
        descricao=dados.descricao,
        local_texto=dados.local_texto,
        inicio=dados.inicio,
        fim=dados.fim,
        vagas=dados.vagas,
        status=dados.status,
        criado_por=criado_por,
    )
    db.add(acao)
    db.flush()

    obrigatorias = set(dados.habilidades_obrigatorias)
    for habilidade_id in sorted(habilidades):
        db.add(AcaoHabilidade(
            acao_id=acao.id,
            habilidade_id=habilidade_id,
            obrigatoria=habilidade_id in obrigatorias,
        ))
    db.flush()

    if dados.status == StatusAcao.PUBLICADA:
        notificacao_service.notificar_compativeis(db, acao, _nome_ong(db, acao.ong_id))

    db.commit()
    db.refresh(acao)
    return acao


def validar_transicao(atual: StatusAcao, novo: StatusAcao) -> None:
    if novo != atual and novo not in TRANSICOES_STATUS[atual]:
        raise ConflitoDeEstado(
            f"Transição de status inválida: {atual.value} -> {novo.value}"
        )


def contar_confirmadas(db: Session, acao_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(Inscricao).where(
            Inscricao.acao_id == acao_id,
            Inscricao.status == StatusInscricao.CONFIRMADA,
        )
    ) or 0


def _descrever_mudancas(antes: dict, acao: AcaoSocial) -> list[str]:
    mudancas = []
    if antes["titulo"] != acao.titulo:
        mudancas.append("título")
    if antes["inicio"] != acao.inicio or antes["fim"] != acao.fim:
        mudancas.append(
            f"data/horário (agora {notificacao_service.formatar_quando(acao.inicio)})"
        )
    if antes["local_texto"] != acao.local_texto or antes["unidade_id"] != acao.unidade_id:
        mudancas.append("local")
    return mudancas


def atualizar(db: Session, acao_id: uuid.UUID, dados: AcaoUpdate) -> AcaoSocial:
    # FOR UPDATE: o trigger de inscrição trava a mesma linha, então uma
    # inscrição concorrente espera esta edição terminar (e vice-versa).
    # Sem isso, reduzir vagas poderia passar enquanto alguém se inscreve.
    acao = obter(db, acao_id, para_atualizar=True)
    mudancas = dados.model_dump(exclude_unset=True)

    status_atual = StatusAcao(acao.status)
    if status_atual in _ESTADOS_FINAIS:
        raise ConflitoDeEstado(f"Ação {status_atual.value} não pode ser editada")

    novo_status = status_atual
    if mudancas.get("status") is not None:
        novo_status = StatusAcao(mudancas["status"])
        validar_transicao(status_atual, novo_status)

    inicio = mudancas.get("inicio") or acao.inicio
    fim = mudancas.get("fim") or acao.fim
    if fim <= inicio:
        raise DadosInvalidos("fim deve ser posterior a inicio")
    if mudancas.get("inicio") is not None and mudancas["inicio"] != acao.inicio:
        _nao_no_passado(mudancas["inicio"])

    if mudancas.get("vagas") is not None:
        confirmadas = contar_confirmadas(db, acao.id)
        if mudancas["vagas"] < confirmadas:
            raise ConflitoDeEstado(
                f"Não é possível reduzir para {mudancas['vagas']} vagas: "
                f"já há {confirmadas} inscrições confirmadas"
            )

    antes = {
        "titulo": acao.titulo, "inicio": acao.inicio, "fim": acao.fim,
        "local_texto": acao.local_texto, "unidade_id": acao.unidade_id,
    }
    for campo, valor in mudancas.items():
        if valor is None and campo in _NAO_NULOS:
            continue
        setattr(acao, campo, valor)
    # Grava a ação antes das notificações: notificar_compativeis lê a
    # linha já atualizada (início/fim) direto no banco.
    db.flush()

    if novo_status != status_atual and novo_status == StatusAcao.CANCELADA:
        notificacao_service.notificar_inscritos(
            db, acao, TipoNotificacao.ACAO_CANCELADA, "Ação cancelada",
            f'A ação "{acao.titulo}" de '
            f"{notificacao_service.formatar_quando(acao.inicio)} foi cancelada pela ONG.",
        )
    else:
        if status_atual == StatusAcao.RASCUNHO and novo_status == StatusAcao.PUBLICADA:
            notificacao_service.notificar_compativeis(db, acao, _nome_ong(db, acao.ong_id))
        alteracoes = _descrever_mudancas(antes, acao)
        if alteracoes:
            notificacao_service.notificar_inscritos(
                db, acao, TipoNotificacao.ACAO_ATUALIZADA, "Ação atualizada",
                f'A ação "{acao.titulo}" teve alteração em: {", ".join(alteracoes)}.',
            )

    db.commit()
    db.refresh(acao)
    return acao
