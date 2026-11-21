"""Perfil do voluntário (dados, habilidades, disponibilidade) e histórico."""
import decimal
import uuid

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.core.exceptions import DadosInvalidos, RecursoNaoEncontrado
from app.models import (
    Habilidade,
    Usuario,
    Voluntario,
    VoluntarioDisponibilidade,
    VoluntarioHabilidade,
)
from app.schemas.voluntario import PerfilUpdate

_CAMPOS_VOLUNTARIO = ("telefone", "data_nascimento", "cidade", "uf", "biografia")


def _voluntario(db: Session, usuario_id: uuid.UUID) -> Voluntario:
    voluntario = db.scalar(select(Voluntario).where(Voluntario.usuario_id == usuario_id))
    if voluntario is None:
        raise RecursoNaoEncontrado("Perfil de voluntário não encontrado")
    return voluntario


def listar_habilidades(db: Session) -> list[Habilidade]:
    return list(db.scalars(select(Habilidade).order_by(Habilidade.categoria, Habilidade.nome)).all())


def obter_perfil(db: Session, usuario: Usuario) -> dict:
    voluntario = _voluntario(db, usuario.id)
    habilidades = db.execute(
        select(
            VoluntarioHabilidade.habilidade_id, VoluntarioHabilidade.nivel,
            Habilidade.nome, Habilidade.categoria,
        )
        .join(Habilidade, Habilidade.id == VoluntarioHabilidade.habilidade_id)
        .where(VoluntarioHabilidade.voluntario_id == voluntario.id)
        .order_by(Habilidade.nome)
    ).mappings().all()
    janelas = db.scalars(
        select(VoluntarioDisponibilidade)
        .where(VoluntarioDisponibilidade.voluntario_id == voluntario.id)
        .order_by(VoluntarioDisponibilidade.dia_semana, VoluntarioDisponibilidade.hora_inicio)
    ).all()
    return {
        "usuario_id": usuario.id,
        "voluntario_id": voluntario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "telefone": voluntario.telefone,
        "data_nascimento": voluntario.data_nascimento,
        "cidade": voluntario.cidade,
        "uf": voluntario.uf,
        "biografia": voluntario.biografia,
        "habilidades": [dict(h) for h in habilidades],
        "disponibilidade": janelas,
    }


def atualizar_perfil(db: Session, usuario: Usuario, dados: PerfilUpdate) -> dict:
    voluntario = _voluntario(db, usuario.id)
    campos = dados.model_dump(exclude_unset=True)

    if campos.get("nome") is not None:
        usuario.nome = campos["nome"].strip()
    for campo in _CAMPOS_VOLUNTARIO:
        if campo in campos:
            setattr(voluntario, campo, campos[campo])

    if dados.habilidades is not None:
        # Última ocorrência de cada habilidade vence (evita violar a PK).
        niveis = {h.habilidade_id: h.nivel for h in dados.habilidades}
        if niveis:
            existentes = db.scalar(
                select(func.count()).select_from(Habilidade).where(Habilidade.id.in_(niveis))
            )
            if existentes != len(niveis):
                raise DadosInvalidos("Habilidade inexistente na lista informada")
        db.execute(delete(VoluntarioHabilidade).where(
            VoluntarioHabilidade.voluntario_id == voluntario.id
        ))
        db.add_all([
            VoluntarioHabilidade(voluntario_id=voluntario.id, habilidade_id=hid, nivel=nivel)
            for hid, nivel in niveis.items()
        ])

    if dados.disponibilidade is not None:
        janelas = {
            (j.dia_semana, j.hora_inicio, j.hora_fim) for j in dados.disponibilidade
        }
        db.execute(delete(VoluntarioDisponibilidade).where(
            VoluntarioDisponibilidade.voluntario_id == voluntario.id
        ))
        db.add_all([
            VoluntarioDisponibilidade(
                voluntario_id=voluntario.id, dia_semana=dia, hora_inicio=ini, hora_fim=fim
            )
            for dia, ini, fim in sorted(janelas)
        ])

    db.commit()
    return obter_perfil(db, usuario)


def historico(db: Session, usuario: Usuario) -> dict:
    """Participações em ações encerradas (concluídas, ou já terminadas e
    não canceladas), a partir da view vw_historico_voluntario."""
    voluntario = _voluntario(db, usuario.id)
    linhas = db.execute(text("""
        SELECT h.acao_id, h.acao_titulo, h.ong_nome, h.inicio, h.fim,
               a.status AS status_acao, h.status_inscricao,
               h.check_in, h.check_out, h.horas_computadas
          FROM public.vw_historico_voluntario h
          JOIN public.acao_social a ON a.id = h.acao_id
         WHERE h.voluntario_id = :voluntario_id
           AND h.status_inscricao = 'confirmada'
           AND (a.status = 'concluida'
                OR (a.status <> 'cancelada' AND a.status <> 'rascunho' AND h.fim < now()))
         ORDER BY h.inicio DESC, h.acao_id
    """), {"voluntario_id": voluntario.id}).mappings().all()
    itens = [dict(linha) for linha in linhas]
    presencas = sum(1 for i in itens if i["check_in"] is not None)
    total_horas = sum(
        (i["horas_computadas"] or decimal.Decimal(0) for i in itens), decimal.Decimal(0)
    )
    return {
        "itens": itens,
        "total_acoes": len(itens),
        "presencas": presencas,
        "ausencias": len(itens) - presencas,
        "total_horas": total_horas,
    }
