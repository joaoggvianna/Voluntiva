from . import auth as _auth
from . import services as _services
from .errors import BadRequest, Unauthorized

# Os adapters sao resolvidos em tempo de chamada, nao no import.
# Assim os mocks continuam sendo o padrao (a suite roda sem banco) e o
# servidor real troca por implementacoes ligadas ao Postgres no boot.


def set_auth(modulo):
    """Substitui o verificador de token. Ver protocol/auth_db.py."""
    global _auth
    _auth = modulo


def set_services(modulo):
    """Substitui as regras de negocio. Ver protocol/services_db.py."""
    global _services
    _services = modulo

def _require_auth(session):
    if not session.authenticated:
        raise Unauthorized("Authenticate first")

def handle_request(request, session):
    cmd = request.command

    if cmd == "PING":
        return 200, "OK", {"message": "PONG"}

    if cmd == "AUTH":
        # A failed reauthentication must not retain the previous identity.
        session.user_id = None
        session.role = None
        session.authenticated = False
        token = request.payload.get("token")
        if not isinstance(token, str) or not token or len(token) > 8192:
            raise BadRequest("token is required")
        identity = _auth.verify_access_token(token)
        session.user_id = identity["user_id"]
        session.role = identity["role"]
        session.authenticated = True
        return 200, "AUTHENTICATED", {
            "user_id": session.user_id,
            "role": session.role,
        }

    _require_auth(session)

    if cmd == "LIST_ACTIONS":
        return 200, "OK", {"actions": _services.list_actions()}

    if cmd == "REGISTER_ACTION":
        action_id = request.payload.get("action_id")
        if type(action_id) is not int or action_id <= 0:
            raise BadRequest("action_id must be a positive integer")
        data = _services.register_action(session.user_id, session.role, action_id)
        return 201, "CREATED", data

    if cmd == "CANCEL_REGISTRATION":
        action_id = request.payload.get("action_id")
        if type(action_id) is not int or action_id <= 0:
            raise BadRequest("action_id must be a positive integer")
        data = _services.cancel_registration(session.user_id, session.role, action_id)
        return 200, "OK", data

    raise BadRequest("Unknown command")
