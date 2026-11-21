"""ONGs e unidades: cadastro, consulta pública e manutenção.

A autorização (quem pode alterar qual ONG/unidade) fica nas rotas, via
app/api/autorizacao.py.
"""
import uuid

from sqlalchemy import exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflitoDeEstado, DadosInvalidos, RecursoNaoEncontrado
from app.core.security import hash_senha
from app.models import (
    AcaoSocial,
    CausaSocial,
    Ong,
    OngMembro,
    PapelMembro,
    StatusAcao,
    TipoUsuario,
    Unidade,
    Usuario,
)
from app.schemas.ong import OngCadastro, OngUpdate, UnidadeCreate, UnidadeUpdate

_ACAO_ABERTA = (StatusAcao.PUBLICADA, StatusAcao.EM_ANDAMENTO)


def _like(busca: str) -> str:
    escapado = busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


# ---------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------

def cadastrar(db: Session, dados: OngCadastro) -> Usuario:
    """Cria, numa transação: usuário (tipo ong), ONG, vínculo de
    proprietário com acesso à ONG inteira e, opcionalmente, a unidade Sede."""
    if db.scalar(select(Usuario.id).where(func.lower(Usuario.email) == dados.email.lower())):
        raise DadosInvalidos("Já existe uma conta com este e-mail")
    if dados.cnpj and db.scalar(select(Ong.id).where(Ong.cnpj == dados.cnpj)):
        raise DadosInvalidos("Já existe uma ONG com este CNPJ")

    usuario = Usuario(
        nome=dados.nome_responsavel or dados.nome[:120],
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        tipo=TipoUsuario.ONG,
    )
    ong = Ong(
        nome=dados.nome,
        cnpj=dados.cnpj,
        email_contato=dados.email,
        telefone=dados.telefone,
        descricao=dados.descricao,
        site=dados.site,
        causa=dados.causa,
    )
    db.add_all([usuario, ong])
    db.flush()

    if dados.sede is not None:
        db.add(Unidade(ong_id=ong.id, **dados.sede.model_dump()))
    db.add(OngMembro(
        usuario_id=usuario.id, ong_id=ong.id, unidade_id=None,
        papel=PapelMembro.PROPRIETARIO,
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        # Corrida com outro cadastro do mesmo e-mail/CNPJ entre o SELECT e o INSERT.
        db.rollback()
        raise DadosInvalidos("Já existe uma conta com este e-mail ou CNPJ") from exc
    db.refresh(usuario)
    return usuario


# ---------------------------------------------------------------------
# Consulta pública
# ---------------------------------------------------------------------

def _montar_publicas(db: Session, ongs: list[Ong]) -> list[dict]:
    """Anexa unidades ativas e contagem de ações abertas: duas consultas
    no total, qualquer que seja o número de ONGs (sem N+1)."""
    if not ongs:
        return []
    ids = [o.id for o in ongs]
    unidades = db.scalars(
        select(Unidade)
        .where(Unidade.ong_id.in_(ids), Unidade.ativo.is_(True))
        .order_by(Unidade.nome)
    ).all()
    abertas = dict(db.execute(
        select(AcaoSocial.ong_id, func.count())
        .where(AcaoSocial.ong_id.in_(ids), AcaoSocial.status.in_(_ACAO_ABERTA),
               AcaoSocial.fim >= func.now())
        .group_by(AcaoSocial.ong_id)
    ).all())
    por_ong: dict[uuid.UUID, list[Unidade]] = {i: [] for i in ids}
    for unidade in unidades:
        por_ong[unidade.ong_id].append(unidade)
    return [
        {
            "id": o.id, "nome": o.nome, "descricao": o.descricao, "site": o.site,
            "email_contato": o.email_contato, "telefone": o.telefone, "causa": o.causa,
            "unidades": por_ong[o.id], "acoes_abertas": abertas.get(o.id, 0),
        }
        for o in ongs
    ]


def listar_publicas(
    db: Session,
    *,
    busca: str | None = None,
    uf: str | None = None,
    causa: CausaSocial | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[dict]:
    consulta = select(Ong).where(Ong.ativo.is_(True))
    busca = (busca or "").strip()
    if busca:
        padrao = _like(busca)
        cidade_casa = exists().where(
            Unidade.ong_id == Ong.id, Unidade.cidade.ilike(padrao, escape="\\")
        )
        consulta = consulta.where(or_(
            Ong.nome.ilike(padrao, escape="\\"),
            Ong.descricao.ilike(padrao, escape="\\"),
            cidade_casa,
        ))
    if causa is not None:
        consulta = consulta.where(Ong.causa == causa)
    if uf:
        consulta = consulta.where(exists().where(
            Unidade.ong_id == Ong.id, Unidade.uf == uf, Unidade.ativo.is_(True)
        ))
    ongs = list(db.scalars(
        consulta.order_by(Ong.nome, Ong.id).limit(limite).offset(offset)
    ).all())
    return _montar_publicas(db, ongs)


def obter_publica(db: Session, ong_id: uuid.UUID) -> dict:
    ong = db.get(Ong, ong_id)
    if ong is None or not ong.ativo:
        raise RecursoNaoEncontrado("ONG não encontrada")
    return _montar_publicas(db, [ong])[0]


def minhas(db: Session, usuario: Usuario) -> list[dict]:
    """ONGs que o usuário gere. Três consultas no total (vínculos, ONGs,
    unidades), em vez de duas por ONG como antes."""
    if usuario.tipo not in (TipoUsuario.ONG, TipoUsuario.ADMIN):
        return []

    if usuario.tipo == TipoUsuario.ADMIN:
        ongs = db.scalars(select(Ong).where(Ong.ativo.is_(True)).order_by(Ong.nome)).all()
        vinculos_por_ong: dict[uuid.UUID, list[OngMembro]] = {}
    else:
        vinculos = db.scalars(
            select(OngMembro).where(OngMembro.usuario_id == usuario.id)
        ).all()
        vinculos_por_ong = {}
        for vinculo in vinculos:
            vinculos_por_ong.setdefault(vinculo.ong_id, []).append(vinculo)
        if not vinculos_por_ong:
            return []
        ongs = db.scalars(
            select(Ong)
            .where(Ong.id.in_(vinculos_por_ong), Ong.ativo.is_(True))
            .order_by(Ong.nome)
        ).all()

    ids = [o.id for o in ongs]
    unidades = db.scalars(
        select(Unidade)
        .where(Unidade.ong_id.in_(ids), Unidade.ativo.is_(True))
        .order_by(Unidade.nome)
    ).all() if ids else []

    resultado = []
    for ong in ongs:
        vinculos = vinculos_por_ong.get(ong.id, [])
        acesso_total = usuario.tipo == TipoUsuario.ADMIN or any(
            v.unidade_id is None for v in vinculos
        )
        permitidas = {v.unidade_id for v in vinculos}
        visiveis = [
            u for u in unidades
            if u.ong_id == ong.id and (acesso_total or u.id in permitidas)
        ]
        # O papel mais alto entre os vínculos (proprietário > gestor > operador).
        papeis = [PapelMembro(v.papel) for v in vinculos]
        ordem = [PapelMembro.PROPRIETARIO, PapelMembro.GESTOR, PapelMembro.OPERADOR]
        papel = next((p.value for p in ordem if p in papeis), None)
        resultado.append({
            "id": ong.id, "nome": ong.nome, "acesso_total": acesso_total, "papel": papel,
            "unidades": [
                {"id": u.id, "nome": u.nome, "cidade": u.cidade, "uf": u.uf} for u in visiveis
            ],
        })
    return resultado


# ---------------------------------------------------------------------
# Manutenção
# ---------------------------------------------------------------------

def atualizar(db: Session, ong_id: uuid.UUID, dados: OngUpdate) -> dict:
    ong = db.get(Ong, ong_id)
    if ong is None or not ong.ativo:
        raise RecursoNaoEncontrado("ONG não encontrada")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(ong, campo, valor)
    db.commit()
    return obter_publica(db, ong_id)


def listar_unidades(db: Session, ong_id: uuid.UUID) -> list[Unidade]:
    return list(db.scalars(
        select(Unidade)
        .where(Unidade.ong_id == ong_id, Unidade.ativo.is_(True))
        .order_by(Unidade.nome)
    ).all())


def obter_unidade(db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.ong_id != ong_id or not unidade.ativo:
        raise RecursoNaoEncontrado("Unidade não encontrada")
    return unidade


def _commit_unidade(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "unidade_nome_por_ong_uk" in str(exc.orig):
            raise ConflitoDeEstado("Já existe uma unidade com este nome nesta ONG") from exc
        raise


def criar_unidade(db: Session, ong_id: uuid.UUID, dados: UnidadeCreate) -> Unidade:
    if db.get(Ong, ong_id) is None:
        raise RecursoNaoEncontrado("ONG não encontrada")
    unidade = Unidade(ong_id=ong_id, **dados.model_dump())
    db.add(unidade)
    _commit_unidade(db)
    db.refresh(unidade)
    return unidade


def atualizar_unidade(
    db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID, dados: UnidadeUpdate
) -> Unidade:
    unidade = obter_unidade(db, ong_id, unidade_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        if valor is None and campo in ("nome", "cidade", "uf"):
            continue  # NOT NULL: None significa "não mexer"
        setattr(unidade, campo, valor)
    _commit_unidade(db)
    db.refresh(unidade)
    return unidade


def remover_unidade(db: Session, ong_id: uuid.UUID, unidade_id: uuid.UUID) -> None:
    """Remove a unidade. Com ações vinculadas, recusa: apagar mudaria o
    local de ações (FK SET NULL) e o histórico dos voluntários."""
    unidade = obter_unidade(db, ong_id, unidade_id)
    tem_acoes = db.scalar(
        select(func.count()).select_from(AcaoSocial).where(AcaoSocial.unidade_id == unidade_id)
    )
    if tem_acoes:
        raise ConflitoDeEstado("Esta unidade possui ações vinculadas e não pode ser removida")
    db.delete(unidade)
    db.commit()
