"""Organizações e unidades que o usuário autenticado pode administrar."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import usuario_atual
from app.db.session import get_db
from app.models import Ong, OngMembro, TipoUsuario, Unidade, Usuario

router = APIRouter(prefix="/ongs", tags=["ONGs"])


@router.get("/minhas")
def minhas_ongs(
    db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_atual)
):
    if usuario.tipo not in (TipoUsuario.ONG, TipoUsuario.ADMIN):
        return []
    query = select(Ong).where(Ong.ativo.is_(True))
    if usuario.tipo != TipoUsuario.ADMIN:
        query = query.join(OngMembro, OngMembro.ong_id == Ong.id).where(
            OngMembro.usuario_id == usuario.id
        ).distinct()
    ongs = db.scalars(query.order_by(Ong.nome)).all()
    resultado = []
    for ong in ongs:
        vinculos = db.scalars(
            select(OngMembro).where(
                OngMembro.usuario_id == usuario.id,
                OngMembro.ong_id == ong.id,
            )
        ).all() if usuario.tipo != TipoUsuario.ADMIN else []
        acesso_total = usuario.tipo == TipoUsuario.ADMIN or any(
            membro.unidade_id is None for membro in vinculos
        )
        unidades = db.scalars(
            select(Unidade).where(
                Unidade.ong_id == ong.id, Unidade.ativo.is_(True)
            ).order_by(Unidade.nome)
        ).all()
        if not acesso_total:
            permitidas = {m.unidade_id for m in vinculos}
            unidades = [u for u in unidades if u.id in permitidas]
        resultado.append({
            "id": str(ong.id), "nome": ong.nome,
            "unidades": [
                {"id": str(u.id), "nome": u.nome, "cidade": u.cidade, "uf": u.uf}
                for u in unidades
            ],
        })
    return resultado
