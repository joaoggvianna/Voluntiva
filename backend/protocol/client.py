import json
import socket
import ssl
import uuid
import re
import time

from .config import CONFIG
from .errors import BadRequest
from .framing import read_headers, read_payload, validate_identifier, validate_command

def build_request(command: str, payload: dict | None = None) -> bytes:
    command = validate_command(command)
    payload = payload or {}
    body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    rid = str(uuid.uuid4())
    header = (
        "VAP/1.0\r\n"
        f"COMMAND: {command}\r\n"
        f"REQUEST-ID: {rid}\r\n"
        f"CONTENT-LENGTH: {len(body)}\r\n"
        "\r\n"
    ).encode("utf-8")
    return header + body

def read_response(sock, expected_request_id=None):
    deadline = time.monotonic() + CONFIG.message_timeout
    status, headers = read_headers(sock, deadline)
    if not re.fullmatch(r"VAP/1\.0 [1-5][0-9]{2} [A-Z_]{1,64}", status):
        raise BadRequest("Invalid response status")
    rid = validate_identifier(headers.get("REQUEST-ID"))
    if expected_request_id is not None and rid != expected_request_id:
        raise BadRequest("Response REQUEST-ID mismatch")
    payload = read_payload(sock, headers, CONFIG.max_message_size, deadline)
    return status, headers, payload


def connect():
    sock = socket.create_connection((CONFIG.host, CONFIG.port), timeout=CONFIG.auth_timeout)
    if CONFIG.use_tls:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # DEV ONLY
        try:
            sock = context.wrap_socket(sock, server_hostname=CONFIG.host)
        except Exception:
            sock.close()
            raise
    return sock

def main():
    with connect() as sock:
        tests = [
            ("PING", {}),
            ("AUTH", {"token": "token-volunteer"}),
            ("LIST_ACTIONS", {}),
            ("REGISTER_ACTION", {"action_id": 1}),
        ]

        for command, payload in tests:
            raw = build_request(command, payload)
            rid = raw.split(b"REQUEST-ID: ", 1)[1].split(b"\r\n", 1)[0].decode("ascii")
            sock.settimeout(CONFIG.write_timeout)
            sock.sendall(raw)
            status, _, body = read_response(sock, expected_request_id=rid)
            print(status)
            print(json.dumps(body, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
