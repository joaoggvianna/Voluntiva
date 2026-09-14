import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest

from protocol import server, services
from protocol.client import build_request, read_response
from protocol.config import ProtocolConfig
from protocol.errors import BadRequest, Conflict, Unauthorized, PayloadTooLarge
from protocol.framing import read_message, build_response
from protocol.handlers import handle_request
from protocol.models import Request, Session


class MemorySocket:
    def __init__(self, data):
        self.data = data

    def recv(self, size):
        chunk, self.data = self.data[:size], self.data[size:]
        return chunk

    def settimeout(self, timeout):
        self.timeout = timeout


def frame(body=b"{}", headers=b"", rid=b"abc", length=None):
    length = str(len(body)).encode() if length is None else length
    return (b"VAP/1.0\r\nCOMMAND: PING\r\nREQUEST-ID: " + rid +
            b"\r\nCONTENT-LENGTH: " + length + b"\r\n" + headers + b"\r\n" + body)


@pytest.mark.parametrize("raw", [
    frame(headers=b"content-length: 2\r\n"),
    frame(headers=b"COMMAND: AUTH\r\n"),
    frame(headers=b"bad name: x\r\n"),
    frame(rid=b"bad\x00id"), frame(rid=b"bad\nid"), frame(rid=b"x" * 129),
    frame(rid=b"\xff"), frame(length=b"-1"), frame(length=b"+2"),
    frame(length=b"2_0"), frame(length=b""),
    frame().replace(b"CONTENT-LENGTH: 2\r\n", b""),
    b"VAP/2.0\r\n\r\n", b"a" * 8193,
], ids=[f"header-{i}" for i in range(14)])
def test_rejects_ambiguous_headers(raw):
    with pytest.raises(BadRequest):
        read_message(MemorySocket(raw), 65536)


@pytest.mark.parametrize("body", [
    b'{"x":1,"x":2}', b'{"x":{"a":1,"a":2}}',
    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}',
    b'{"x":"\\ud800"}', b'[]', b'{', b'{"x":"\xff"}',
    b'{"x":' + b'[' * 1100 + b'0' + b']' * 1100 + b'}',
    b'{"x":' + b'[' * 34 + b'0' + b']' * 34 + b'}',
], ids=[f"json-{i}" for i in range(11)])
def test_rejects_unsafe_json(body):
    with pytest.raises(BadRequest):
        read_message(MemorySocket(frame(body)), 65536)


def test_payload_limit_checked_before_body_read():
    with pytest.raises(PayloadTooLarge):
        read_message(MemorySocket(frame(b"", length=b"65537")), 65536)


def test_truncated_body_fails_instead_of_looping():
    with pytest.raises(ConnectionError):
        read_response(MemorySocket(b"VAP/1.0 200 OK\r\nREQUEST-ID: abc\r\nCONTENT-LENGTH: 10\r\n\r\n{}"))


def test_response_correlation():
    with pytest.raises(BadRequest):
        read_response(MemorySocket(build_response(200, "OK", "wrong", {})), "expected")


@pytest.mark.parametrize("rid", ["abc\r\nINJECTED: yes", "abc\n", "\x00", "x" * 129])
def test_no_response_header_injection(rid):
    with pytest.raises(BadRequest):
        build_response(200, "OK", rid, {})


def test_absolute_read_deadline(monkeypatch):
    from protocol import framing
    ticks = iter([0.0, 0.4, 0.8, 1.2])
    monkeypatch.setattr(framing.time, "monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError):
        read_message(MemorySocket(frame()), 65536, deadline=1.0)


@pytest.mark.parametrize("action_id", [True, False, 0, -1, "1", 1.0, None])
@pytest.mark.parametrize("command", ["REGISTER_ACTION", "CANCEL_REGISTRATION"])
def test_strict_action_id(command, action_id):
    session = Session(user_id="v", role="VOLUNTEER", authenticated=True)
    with pytest.raises(BadRequest):
        handle_request(Request(command, "id", {"action_id": action_id}), session)


def test_failed_reauthentication_clears_identity():
    session = Session(user_id="v", role="VOLUNTEER", authenticated=True)
    with pytest.raises(Unauthorized):
        handle_request(Request("AUTH", "id", {"token": "wrong"}), session)
    assert session == Session()
    with pytest.raises(Unauthorized):
        handle_request(Request("LIST_ACTIONS", "id", {}), session)


@pytest.fixture
def peer(monkeypatch):
    config = replace(server.CONFIG, auth_timeout=0.3, message_timeout=0.3, write_timeout=0.3)
    monkeypatch.setattr(server, "CONFIG", config)
    a, b = socket.socketpair()
    a.settimeout(2)
    worker = threading.Thread(target=server.handle_client, args=(b, ("127.0.0.1", 1)))
    worker.start()
    yield a
    a.close()
    worker.join(2)
    assert not worker.is_alive()


def test_bad_frame_closes_stream_without_executing_following_request(peer, monkeypatch):
    executed = []
    original = server.handle_request
    def track(request, session):
        executed.append(request.command)
        return original(request, session)
    monkeypatch.setattr(server, "handle_request", track)
    peer.sendall(frame(length=b"999999") + build_request("AUTH", {"token": "token-volunteer"}))
    try:
        assert read_response(peer)[0] == "VAP/1.0 413 PAYLOAD_TOO_LARGE"
        assert peer.recv(1) == b""
    except ConnectionResetError:
        # Windows can discard the error reply when closing with unread input.
        pass
    assert executed == []


def test_auth_failure_limit(peer):
    for _ in range(3):
        peer.sendall(build_request("AUTH", {"token": "wrong"}))
        assert read_response(peer)[0] == "VAP/1.0 401 UNAUTHORIZED"
    assert peer.recv(1) == b""


def test_ping_does_not_extend_auth_deadline(peer):
    peer.sendall(build_request("PING"))
    assert read_response(peer)[0] == "VAP/1.0 200 OK"
    assert read_response(peer)[0] == "VAP/1.0 408 TIMEOUT"
    assert peer.recv(1) == b""


def test_business_error_preserves_framing(peer):
    peer.sendall(build_request("LIST_ACTIONS") + build_request("PING"))
    assert read_response(peer)[0] == "VAP/1.0 401 UNAUTHORIZED"
    assert read_response(peer)[2] == {"message": "PONG"}


def test_limiter_bounds_and_releases():
    limiter = server.ConnectionLimiter(2, 1)
    assert limiter.acquire("a")
    assert not limiter.acquire("a")
    assert limiter.acquire("b")
    assert not limiter.acquire("c")
    limiter.release("a")
    assert limiter.acquire("c")
    limiter.release("b")
    limiter.release("c")
    assert limiter.total == 0 and limiter.counts == {}


def test_concurrent_registrations_never_exceed_capacity(monkeypatch):
    monkeypatch.setattr(services, "REGISTRATIONS", set())
    def register(index):
        try:
            services.register_action(f"security-{index}", "VOLUNTEER", 2)
            return True
        except Conflict:
            return False
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(register, range(100)))
    assert sum(results) == 1
    assert len(services.REGISTRATIONS) == 1


def test_action_listing_does_not_expose_mutable_storage():
    result = services.list_actions()
    result[0]["capacity"] = 999
    assert services.ACTIONS[1]["capacity"] == 2


@pytest.mark.parametrize("name,value", [
    ("auth_timeout", float("nan")), ("idle_timeout", float("inf")),
    ("message_timeout", 0), ("write_timeout", -1), ("max_connections", 0),
    ("max_connections_per_ip", -1), ("max_auth_failures", 0), ("port", 65536),
])
def test_invalid_security_config_fails_fast(name, value):
    with pytest.raises(ValueError):
        ProtocolConfig(**{name: value})


def test_request_rate_limit(peer, monkeypatch):
    monkeypatch.setattr(server, "CONFIG", replace(server.CONFIG, max_requests_per_second=2))
    for _ in range(2):
        peer.sendall(build_request("PING"))
        assert read_response(peer)[0] == "VAP/1.0 200 OK"
    peer.sendall(build_request("PING"))
    assert read_response(peer)[0] == "VAP/1.0 400 BAD_REQUEST"
    assert peer.recv(1) == b""


def test_connection_request_budget(monkeypatch):
    monkeypatch.setattr(server, "CONFIG", replace(server.CONFIG, max_requests_per_connection=2))
    a, b = socket.socketpair()
    worker = threading.Thread(target=server.handle_client, args=(b, ("127.0.0.1", 1)))
    worker.start()
    try:
        for _ in range(2):
            a.sendall(build_request("PING"))
            assert read_response(a)[0] == "VAP/1.0 200 OK"
        assert a.recv(1) == b""
    finally:
        a.close()
        worker.join(2)
    assert not worker.is_alive()


def test_handshake_has_timeout_and_closes_socket(monkeypatch):
    monkeypatch.setattr(server, "CONFIG", replace(server.CONFIG, use_tls=True))
    class FailedHandshake:
        closed = False
        def do_handshake(self):
            raise TimeoutError("slow handshake")
        def close(self):
            self.closed = True
    wrapped = FailedHandshake()
    class Context:
        def wrap_socket(self, raw, **kwargs):
            assert raw.gettimeout() == server.CONFIG.auth_timeout
            assert kwargs == {"server_side": True, "do_handshake_on_connect": False}
            return wrapped
    a, b = socket.socketpair()
    try:
        server.handle_client(b, ("127.0.0.1", 1), Context())
        assert wrapped.closed
        assert b.fileno() == -1
    finally:
        a.close()
        b.close()


def test_full_client_flow(peer, monkeypatch):
    monkeypatch.setattr(services, "REGISTRATIONS", set())
    commands = [
        ("PING", {}, "VAP/1.0 200 OK"),
        ("AUTH", {"token": "token-volunteer"}, "VAP/1.0 200 AUTHENTICATED"),
        ("LIST_ACTIONS", {}, "VAP/1.0 200 OK"),
        ("REGISTER_ACTION", {"action_id": 1}, "VAP/1.0 201 CREATED"),
        ("CANCEL_REGISTRATION", {"action_id": 1}, "VAP/1.0 200 OK"),
    ]
    for command, payload, status in commands:
        peer.sendall(build_request(command, payload))
        assert read_response(peer)[0] == status
