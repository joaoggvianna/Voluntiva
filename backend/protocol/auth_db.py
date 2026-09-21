"""Verificador de token real, substituindo o mock de protocol/auth.py.

Fecha o ciclo de autenticação da stack: o cliente TCP obtém o JWT pela API
REST (POST /api/v1/auth/login) e o apresenta ao socket via comando AUTH.
Não existe senha trafegando no protocolo VAP.

Ligado no boot por protocol/__main__.py, via handlers.set_auth().
"""
from __future__ import annotations

import uuid

import jwt

from app.core.security import decodificar_token
from app.db.session import SessionLocal
from app.models import Usuario

from .errors import Unauthorized

# O banco guarda o tipo em minúsculo; o protocolo usa o papel em maiúsculo
# (docs/VAP.md seção 4). A tradução mora aqui e em nenhum outro lugar.
PAPEL_POR_TIPO = {
    "voluntario": "VOLUNTEER",
    "ong": "ONG",
    "admin": "ADMIN",
}


def verify_access_token(token: str) -> dict:
    """Valida o JWT e devolve {"user_id": str, "role": str}.

    Mensagem de erro sempre igual: distinguir "token expirado" de "usuário
    desativado" entrega informação a quem está sondando o servidor.
    """
    try:
        payload = decodificar_token(token, scope_esperado="access")
        usuario_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise Unauthorized("Invalid or expired token") from exc

    # Consulta o banco em vez de confiar no claim "tipo" do token: assim uma
    # conta desativada ou com papel alterado perde acesso na hora, sem
    # esperar o token expirar.
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, usuario_id)
        if usuario is None or not usuario.ativo:
            raise Unauthorized("Invalid or expired token")
        papel = PAPEL_POR_TIPO.get(usuario.tipo.value)
        if papel is None:
            raise Unauthorized("Invalid or expired token")
        return {"user_id": str(usuario.id), "role": papel}
    finally:
        db.close()
