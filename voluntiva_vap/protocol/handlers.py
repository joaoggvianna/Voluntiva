from .auth import verify_access_token
from .errors import BadRequest, Unauthorized
from .services import list_actions, register_action, cancel_registration

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
        identity = verify_access_token(token)
        session.user_id = identity["user_id"]
        session.role = identity["role"]
        session.authenticated = True
        return 200, "AUTHENTICATED", {
            "user_id": session.user_id,
            "role": session.role,
        }

    _require_auth(session)

    if cmd == "LIST_ACTIONS":
        return 200, "OK", {"actions": list_actions()}

    if cmd == "REGISTER_ACTION":
        action_id = request.payload.get("action_id")
        if type(action_id) is not int or action_id <= 0:
            raise BadRequest("action_id must be a positive integer")
        data = register_action(session.user_id, session.role, action_id)
        return 201, "CREATED", data

    if cmd == "CANCEL_REGISTRATION":
        action_id = request.payload.get("action_id")
        if type(action_id) is not int or action_id <= 0:
            raise BadRequest("action_id must be a positive integer")
        data = cancel_registration(session.user_id, session.role, action_id)
        return 200, "OK", data

    raise BadRequest("Unknown command")
