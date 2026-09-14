import socket
from protocol.framing import read_message
from protocol.errors import BadRequest

def test_reads_valid_message():
    a, b = socket.socketpair()
    try:
        raw = (
            b"VAP/1.0\r\n"
            b"COMMAND: PING\r\n"
            b"REQUEST-ID: abc\r\n"
            b"CONTENT-LENGTH: 2\r\n"
            b"\r\n{}"
        )
        a.sendall(raw)
        req = read_message(b, 1024)
        assert req.command == "PING"
        assert req.request_id == "abc"
        assert req.payload == {}
    finally:
        a.close()
        b.close()
