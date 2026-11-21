"""Números da página inicial (públicos)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["estatísticas"])


class Estatisticas(BaseModel):
    ongs: int
    acoes_abertas: int
    voluntarios: int
    participacoes: int


@router.get("/estatisticas", response_model=Estatisticas)
def estatisticas(db: Session = Depends(get_db)):
    """Uma consulta só, com subconsultas escalares."""
    linha = db.execute(text("""
        SELECT
          (SELECT count(*) FROM public.ong WHERE ativo) AS ongs,
          (SELECT count(*) FROM public.acao_social
            WHERE status IN ('publicada', 'em_andamento') AND fim >= now()) AS acoes_abertas,
          (SELECT count(*) FROM public.voluntario v
             JOIN public.usuario u ON u.id = v.usuario_id AND u.ativo) AS voluntarios,
          (SELECT count(*) FROM public.inscricao WHERE status = 'confirmada') AS participacoes
    """)).mappings().one()
    return dict(linha)
