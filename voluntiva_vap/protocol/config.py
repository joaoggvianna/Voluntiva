from dataclasses import dataclass
import os
import math

@dataclass(frozen=True)
class ProtocolConfig:
    host: str = os.getenv("VAP_HOST", "127.0.0.1")
    port: int = int(os.getenv("VAP_PORT", "5050"))
    max_message_size: int = int(os.getenv("VAP_MAX_MESSAGE_SIZE", str(64 * 1024)))
    auth_timeout: float = float(os.getenv("VAP_AUTH_TIMEOUT", "30"))
    idle_timeout: float = float(os.getenv("VAP_IDLE_TIMEOUT", "120"))
    use_tls: bool = os.getenv("VAP_USE_TLS", "false").lower() == "true"
    certfile: str | None = os.getenv("VAP_CERTFILE")
    keyfile: str | None = os.getenv("VAP_KEYFILE")

    message_timeout: float = float(os.getenv("VAP_MESSAGE_TIMEOUT", "30"))
    write_timeout: float = float(os.getenv("VAP_WRITE_TIMEOUT", "5"))
    max_connections: int = int(os.getenv("VAP_MAX_CONNECTIONS", "64"))
    max_connections_per_ip: int = int(os.getenv("VAP_MAX_CONNECTIONS_PER_IP", "8"))
    max_requests_per_connection: int = int(os.getenv("VAP_MAX_REQUESTS_PER_CONNECTION", "1000"))
    max_requests_per_second: int = int(os.getenv("VAP_MAX_REQUESTS_PER_SECOND", "50"))
    max_auth_failures: int = int(os.getenv("VAP_MAX_AUTH_FAILURES", "3"))

    def __post_init__(self):
        for name in ("auth_timeout", "idle_timeout", "message_timeout", "write_timeout"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        for name in ("max_message_size", "max_connections", "max_connections_per_ip",
                     "max_requests_per_connection", "max_requests_per_second", "max_auth_failures"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if not 1 <= self.port <= 65535:
            raise ValueError("Invalid port")

CONFIG = ProtocolConfig()
