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
def register_action(user_id: str, role: str, action_id: int):
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
