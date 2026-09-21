"""Hash de senhas (Argon2id) e emissão/verificação de JWT.

O banco NÃO calcula nem valida hash — ver comentário na tabela `usuario`
da migration. Toda a criptografia de credencial vive aqui.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher(
    time_cost=settings.argon2_time_cost,
    memory_cost=settings.argon2_memory_cost,
    parallelism=settings.argon2_parallelism,
)


def hash_senha(senha_plana: str) -> str:
    """Gera hash Argon2id no formato PHC (começa com '$argon2id$')."""
    return _hasher.hash(senha_plana)


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara em tempo constante. Nunca levanta para senha errada."""
    try:
        return _hasher.verify(senha_hash, senha_plana)
    except (VerifyMismatchError, InvalidHashError):
        return False


def precisa_rehash(senha_hash: str) -> bool:
    """True quando os parâmetros do Argon2 mudaram desde que o hash foi gerado.

    Chame após um login bem-sucedido e regrave o hash se for o caso.
    """
    return _hasher.check_needs_rehash(senha_hash)


# ---------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------

def criar_access_token(
    usuario_id: UUID | str,
    tipo_usuario: str,
    expira_em: timedelta | None = None,
) -> str:
    agora = datetime.now(timezone.utc)
    expiracao = agora + (
        expira_em or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "tipo": tipo_usuario,
        "iat": agora,
        "exp": expiracao,
        "scope": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def criar_refresh_token(usuario_id: UUID | str) -> str:
    agora = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(days=settings.refresh_token_expire_days),
        "scope": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str, scope_esperado: str = "access") -> dict[str, Any]:
    """Decodifica e valida o token.

    Levanta jwt.InvalidTokenError (ou subclasse) em qualquer falha —
    assinatura inválida, expirado, ou scope trocado. Checar o scope impede
    que um refresh token seja usado como access token.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )
    if payload.get("scope") != scope_esperado:
        raise jwt.InvalidTokenError(
            f"scope esperado '{scope_esperado}', recebido '{payload.get('scope')}'"
        )
    return payload
