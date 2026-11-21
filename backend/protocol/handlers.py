from . import auth as _auth
from . import services as _services
from .errors import BadRequest, Forbidden, Unauthorized

# Os adapters sao resolvidos em tempo de chamada, nao no import.
# Assim os mocks continuam sendo o padrao (a suite roda sem banco) e o
# servidor real troca por implementacoes ligadas ao Postgres no boot.

# Papeis que gerem acoes (criar, editar, registrar presenca). O vinculo
# com a ONG da acao e conferido no adapter de servicos.
GESTORES = frozenset({"ONG", "ADMIN"})

# Campos aceitos em CREATE_ACTION / UPDATE_ACTION e o tipo de cada um.
# Campos fora desta lista sao recusados: um erro de digitacao no cliente
# vira 400 em vez de ser ignorado em silencio.
_CAMPOS_ACAO = {
    "org_id": str,
    "unit_id": str,
    "title": str,
    "description": str,
    "location": str,
    "starts_at": str,
    "ends_at": str,
    "capacity": int,
    "skills": list,
    "publish": bool,
    "status": str,
}
_CRIACAO_OBRIGATORIOS = ("title", "starts_at", "ends_at", "capacity")
_EDICAO_PROIBIDOS = ("org_id", "publish", "skills")
_STATUS_EDITAVEIS = frozenset({"OPEN", "IN_PROGRESS", "CLOSED", "CANCELLED"})


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


def _require_role(session, roles, mensagem):
    if session.role not in roles:
        raise Forbidden(mensagem)


def _action_id(payload):
    action_id = payload.get("action_id")
    # type() e nao isinstance(): True/False sao int em Python.
    if type(action_id) is not int or action_id <= 0:
        raise BadRequest("action_id must be a positive integer")
    return action_id


def _campos_acao(payload, *, criacao):
    """Valida forma e tipos; regras de negocio ficam nos services."""
    desconhecidos = set(payload) - set(_CAMPOS_ACAO) - {"action_id"}
    if desconhecidos:
        raise BadRequest(f"Unknown field: {sorted(desconhecidos)[0]}")
    campos = {}
    for nome, tipo in _CAMPOS_ACAO.items():
        if nome not in payload:
            continue
        valor = payload[nome]
        if type(valor) is not tipo:
            raise BadRequest(f"{nome} must be {tipo.__name__}")
        campos[nome] = valor
    if "skills" in campos and not all(type(s) is str for s in campos["skills"]):
        raise BadRequest("skills must be a list of strings")
    if criacao:
        faltando = [c for c in _CRIACAO_OBRIGATORIOS if c not in campos]
        if faltando:
            raise BadRequest(f"{faltando[0]} is required")
        if "status" in campos:
            raise BadRequest("Use publish to choose the initial status")
    else:
        proibidos = [c for c in _EDICAO_PROIBIDOS if c in campos]
        if proibidos:
            raise BadRequest(f"{proibidos[0]} cannot be changed")
        if "status" in campos and campos["status"] not in _STATUS_EDITAVEIS:
            raise BadRequest("Invalid status")
        if not campos:
            raise BadRequest("Nothing to update")
    return campos


def _email(payload):
    email = payload.get("volunteer_email")
    if not isinstance(email, str) or "@" not in email or len(email) > 320:
        raise BadRequest("volunteer_email is required")
    return email.strip()


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
    payload = request.payload

    if cmd == "LIST_ACTIONS":
        return 200, "OK", {"actions": _services.list_actions()}

    if cmd == "REGISTER_ACTION":
        waitlist = payload.get("waitlist", False)
        if type(waitlist) is not bool:
            raise BadRequest("waitlist must be bool")
        action_id = _action_id(payload)
        if waitlist:
            data = _services.register_action(session.user_id, session.role, action_id, waitlist=True)
        else:
            data = _services.register_action(session.user_id, session.role, action_id)
        return 201, "CREATED", data

    if cmd == "CANCEL_REGISTRATION":
        data = _services.cancel_registration(session.user_id, session.role, _action_id(payload))
        return 200, "OK", data

    if cmd == "CREATE_ACTION":
        _require_role(session, GESTORES, "Only organizations can create actions")
        data = _services.create_action(session.user_id, session.role, _campos_acao(payload, criacao=True))
        return 201, "CREATED", data

    if cmd == "UPDATE_ACTION":
        _require_role(session, GESTORES, "Only organizations can update actions")
        action_id = _action_id(payload)
        campos = _campos_acao(payload, criacao=False)
        data = _services.update_action(session.user_id, session.role, action_id, campos)
        return 200, "OK", data

    if cmd in ("CHECK_IN", "CHECK_OUT"):
        _require_role(session, GESTORES, "Only organizations can record attendance")
        action_id = _action_id(payload)
        email = _email(payload)
        funcao = _services.check_in if cmd == "CHECK_IN" else _services.check_out
        data = funcao(session.user_id, session.role, action_id, email)
        return (201, "CREATED", data) if cmd == "CHECK_IN" else (200, "OK", data)

    if cmd == "LIST_NOTIFICATIONS":
        unread_only = payload.get("unread_only", False)
        limit = payload.get("limit", 20)
        if type(unread_only) is not bool:
            raise BadRequest("unread_only must be bool")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise BadRequest("limit must be an integer between 1 and 100")
        data = _services.list_notifications(session.user_id, unread_only=unread_only, limit=limit)
        return 200, "OK", data

    raise BadRequest("Unknown command")
