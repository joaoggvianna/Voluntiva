from dataclasses import dataclass
from typing import Any

@dataclass
class Request:
    command: str
    request_id: str
    payload: dict[str, Any]

@dataclass
class Session:
    user_id: str | None = None
    role: str | None = None
    authenticated: bool = False
