import json
import math
import re
import time

from .errors import BadRequest, PayloadTooLarge
from .models import Request

PROTOCOL_NAME = "VAP/1.0"
HEADER_END = b"\r\n\r\n"
MAX_HEADER_SIZE = 8192


def validate_identifier(value):
    # Preserve existing short IDs while excluding controls and header injection.
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
        raise BadRequest("Invalid REQUEST-ID")
    return value


def validate_command(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_]{1,64}", value):
        raise BadRequest("Invalid COMMAND")
    return value.upper()


def _recv(sock, size, deadline):
    if deadline is not None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Message deadline exceeded")
        sock.settimeout(remaining)
    chunk = sock.recv(size)
    if not chunk:
        raise ConnectionError("Connection closed while reading message")
    return chunk


def _read_exact(sock, n, deadline=None):
    chunks = []
    while n:
        chunk = _recv(sock, min(4096, n), deadline)
        chunks.append(chunk)
        n -= len(chunk)
    return b"".join(chunks)


def read_headers(sock, deadline=None):
    header = bytearray()
    while not header.endswith(HEADER_END):
        header.extend(_recv(sock, 1, deadline))
        if len(header) > MAX_HEADER_SIZE:
            raise BadRequest("Header too large")
    try:
        lines = header[:-4].decode("ascii").split("\r\n")
    except UnicodeDecodeError as exc:
        raise BadRequest("Invalid header encoding") from exc
    headers = {}
    for line in lines[1:]:
        if ":" not in line:
            raise BadRequest("Malformed header")
        key, value = line.split(":", 1)
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,63}", key):
            raise BadRequest("Invalid header name")
        key = key.upper()
        if key in headers:
            raise BadRequest("Duplicate header")
        if any(ord(char) < 32 or ord(char) > 126 for char in value):
            raise BadRequest("Invalid header value")
        headers[key] = value.strip(" ")
    return lines[0], headers


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON number")


def _validate_json_tree(payload):
    pending = [(payload, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 32:
            raise ValueError("JSON nesting too deep")
        if isinstance(value, str):
            value.encode("utf-8")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Non-finite JSON number")
        elif isinstance(value, dict):
            pending.extend((item, depth + 1) for item in value.values())
            pending.extend((key, depth + 1) for key in value)
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)


def read_payload(sock, headers, maximum, deadline=None):
    length = headers.get("CONTENT-LENGTH", "")
    if not re.fullmatch(r"[0-9]{1,10}", length):
        raise BadRequest("Invalid or missing CONTENT-LENGTH")
    length = int(length)
    if length > maximum:
        raise PayloadTooLarge("Payload exceeds maximum size")
    body = _read_exact(sock, length, deadline)
    try:
        payload = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant) if body else {}
        if not isinstance(payload, dict):
            raise ValueError("Expected JSON object")
        _validate_json_tree(payload)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise BadRequest("Invalid JSON object payload") from exc
    return payload


def read_message(sock, max_message_size, deadline=None):
    version, headers = read_headers(sock, deadline)
    if version != PROTOCOL_NAME:
        raise BadRequest("Invalid protocol version")
    command = validate_command(headers.get("COMMAND"))
    request_id = validate_identifier(headers.get("REQUEST-ID"))
    payload = read_payload(sock, headers, max_message_size, deadline)
    return Request(command=command, request_id=request_id, payload=payload)


def build_response(code, label, request_id, payload=None):
    validate_identifier(request_id)
    if type(code) is not int or not 100 <= code <= 599 or not re.fullmatch(r"[A-Z_]{1,64}", label):
        raise BadRequest("Invalid response status")
    body = json.dumps(payload if payload is not None else {}, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")
    return (f"{PROTOCOL_NAME} {code} {label}\r\n"
            f"REQUEST-ID: {request_id}\r\n"
            f"CONTENT-LENGTH: {len(body)}\r\n\r\n").encode("ascii") + body
