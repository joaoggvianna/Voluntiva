"""
Adapter de autenticação.

Em produção, substitua verify_access_token pela validação real do token do
Supabase Auth. A função deve retornar um dicionário com:
    {"user_id": "...", "role": "VOLUNTEER" | "ONG" | "ADMIN"}

O mock abaixo existe para permitir testar o protocolo isoladamente.
"""

from .errors import Unauthorized

MOCK_TOKENS = {
    "token-volunteer": {"user_id": "volunteer-1", "role": "VOLUNTEER"},
    "token-ong": {"user_id": "ong-1", "role": "ONG"},
    "token-admin": {"user_id": "admin-1", "role": "ADMIN"},
}

def verify_access_token(token: str) -> dict:
    identity = MOCK_TOKENS.get(token)
    if not identity:
        raise Unauthorized("Invalid or expired token")
    return identity
