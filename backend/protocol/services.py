"""
Adapter temporário das regras de negócio.

Na integração real, estes métodos devem chamar os mesmos services usados
pelo FastAPI. Assim, REST e VAP compartilham a mesma regra de negócio.
"""

from functools import wraps
from threading import RLock

from .errors import Conflict, Forbidden, NotFound

ACTIONS = {
    1: {"id": 1, "title": "Mutirão de Limpeza", "status": "OPEN", "capacity": 2},
    2: {"id": 2, "title": "Apoio Escolar", "status": "OPEN", "capacity": 1},
}
REGISTRATIONS: set[tuple[str, int]] = set()

_LOCK = RLock()


def _synchronized(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with _LOCK:
            return function(*args, **kwargs)
    return wrapped


@_synchronized
def list_actions():
    return [action.copy() for action in ACTIONS.values()]

@_synchronized
def register_action(user_id: str, role: str, action_id: int, waitlist: bool = False):
    if role != "VOLUNTEER":
        raise Forbidden("Only volunteers can register")

    action = ACTIONS.get(action_id)
    if not action:
        raise NotFound("Action not found")

    if action["status"] != "OPEN":
        raise Conflict("Action is not open")

    key = (user_id, action_id)
    if key in REGISTRATIONS:
        raise Conflict("Already registered")

    total = sum(1 for _, aid in REGISTRATIONS if aid == action_id)
    if total >= action["capacity"]:
        if waitlist:
            return {"action_id": action_id, "status": "WAITLISTED"}
        raise Conflict("Action is full")

    REGISTRATIONS.add(key)
    return {"action_id": action_id, "status": "REGISTERED"}

@_synchronized
def cancel_registration(user_id: str, role: str, action_id: int):
    if role != "VOLUNTEER":
        raise Forbidden("Only volunteers can cancel registrations")

    key = (user_id, action_id)
    if key not in REGISTRATIONS:
        raise NotFound("Registration not found")

    REGISTRATIONS.remove(key)
    return {"action_id": action_id, "status": "CANCELLED"}


# ---------------------------------------------------------------------
# Gestão de ações, presença e notificações (mock em memória)
#
# Só para testar o protocolo sem banco: as regras reais (permissão por
# ONG, transições de status, lotação) estão em protocol/services_db.py,
# que delega para app/services.
# ---------------------------------------------------------------------

ATTENDANCE: dict[tuple[int, str], dict] = {}
NOTIFICATIONS: dict[str, list[dict]] = {}


@_synchronized
def create_action(user_id: str, role: str, fields: dict):
    action_id = max(ACTIONS, default=0) + 1
    ACTIONS[action_id] = {
        "id": action_id,
        "title": fields["title"],
        "status": "OPEN" if fields.get("publish") else "DRAFT",
        "capacity": fields["capacity"],
    }
    return ACTIONS[action_id].copy()


@_synchronized
def update_action(user_id: str, role: str, action_id: int, fields: dict):
    action = ACTIONS.get(action_id)
    if not action:
        raise NotFound("Action not found")
    if action["status"] in ("CLOSED", "CANCELLED"):
        raise Conflict("Action can no longer be changed")
    if "title" in fields:
        action["title"] = fields["title"]
    if "capacity" in fields:
        action["capacity"] = fields["capacity"]
    if "status" in fields:
        action["status"] = fields["status"]
    return action.copy()


@_synchronized
def check_in(user_id: str, role: str, action_id: int, email: str):
    if action_id not in ACTIONS:
        raise NotFound("Action not found")
    key = (action_id, email.lower())
    if key in ATTENDANCE:
        raise Conflict("Check-in already recorded")
    ATTENDANCE[key] = {"action_id": action_id, "volunteer_email": email,
                       "check_in": "2026-01-01T10:00:00+00:00", "check_out": None, "hours": None}
    return ATTENDANCE[key].copy()


@_synchronized
def check_out(user_id: str, role: str, action_id: int, email: str):
    registro = ATTENDANCE.get((action_id, email.lower()))
    if registro is None:
        raise NotFound("No check-in for this registration")
    if registro["check_out"] is not None:
        raise Conflict("Check-out already recorded")
    registro.update(check_out="2026-01-01T12:00:00+00:00", hours=2.0)
    return registro.copy()


@_synchronized
def list_notifications(user_id: str, *, unread_only: bool = False, limit: int = 20):
    itens = NOTIFICATIONS.get(user_id, [])
    if unread_only:
        itens = [n for n in itens if not n["read"]]
    return {
        "unread": sum(1 for n in NOTIFICATIONS.get(user_id, []) if not n["read"]),
        "notifications": [n.copy() for n in itens[:limit]],
    }
