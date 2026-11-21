"""Cliente de linha de comando do VAP.

Uso:
    # demonstração contra o servidor de mocks (python -m protocol.server)
    python -m protocol.client

    # um comando contra o servidor real (python -m protocol), com o JWT
    # obtido em POST /api/v1/auth/login
    python -m protocol.client --token <JWT> LIST_ACTIONS
    python -m protocol.client --token <JWT> REGISTER_ACTION '{"action_id": 1}'
    python -m protocol.client --token <JWT> LIST_NOTIFICATIONS '{"unread_only": true}'

O token também pode vir da variável de ambiente VAP_TOKEN, para não
ficar no histórico do shell.
"""
import argparse
import json
import os
import re
import socket
import ssl
import time
import uuid

from .config import CONFIG
from .errors import BadRequest
from .framing import read_headers, read_payload, validate_command, validate_identifier


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


def send(sock, command: str, payload: dict | None = None):
    raw = build_request(command, payload)
    rid = raw.split(b"REQUEST-ID: ", 1)[1].split(b"\r\n", 1)[0].decode("ascii")
    sock.settimeout(CONFIG.write_timeout)
    sock.sendall(raw)
    return read_response(sock, expected_request_id=rid)


def _imprimir(status, body):
    print(status)
    print(json.dumps(body, indent=2, ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Cliente do protocolo VAP")
    parser.add_argument("--token", default=os.environ.get("VAP_TOKEN"),
                        help="JWT de acesso (padrão: variável VAP_TOKEN)")
    parser.add_argument("command", nargs="?", help="comando, ex.: LIST_ACTIONS")
    parser.add_argument("payload", nargs="?", default="{}", help="payload JSON do comando")
    args = parser.parse_args(argv)

    with connect() as sock:
        if args.command is None:
            # Demonstração contra os mocks de protocol/auth.py e services.py.
            demo = [
                ("PING", {}),
                ("AUTH", {"token": args.token or "token-volunteer"}),
                ("LIST_ACTIONS", {}),
                ("REGISTER_ACTION", {"action_id": 1}),
            ]
            for command, payload in demo:
                _imprimir(*_sem_cabecalhos(send(sock, command, payload)))
            return

        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as exc:
            parser.error(f"payload não é JSON válido: {exc}")
        if not isinstance(payload, dict):
            parser.error("payload deve ser um objeto JSON")
        if args.token:
            status, _, body = send(sock, "AUTH", {"token": args.token})
            if not status.startswith("VAP/1.0 200"):
                _imprimir(status, body)
                return
        _imprimir(*_sem_cabecalhos(send(sock, args.command, payload)))


def _sem_cabecalhos(resposta):
    status, _, body = resposta
    return status, body


if __name__ == "__main__":
    main()
