"""Dependências compartilhadas pelas rotas."""
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decodificar_token
from app.db.session import get_db
from app.models import TipoUsuario, Usuario

_bearer = HTTPBearer(auto_error=True)


def usuario_atual(
    credencial: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    erro = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(credencial.credentials, scope_esperado="access")
        usuario_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise erro

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise erro
    return usuario


def exigir_tipo(*tipos: TipoUsuario):
    """Fábrica de dependência que restringe a rota a certos tipos de usuário."""
    def _verificar(usuario: Usuario = Depends(usuario_atual)) -> Usuario:
        if usuario.tipo not in tipos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão para esta operação",
            )
        return usuario
    return _verificar
