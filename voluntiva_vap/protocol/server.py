import logging
import socket
import ssl
import threading
import time
import uuid

from .config import CONFIG
from .errors import BadRequest, Unauthorized, VAPError
from .framing import read_message, build_response
from .handlers import handle_request
from .models import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s message=%(message)s")
logger = logging.getLogger("vap")


def _tls_context():
    if not CONFIG.use_tls:
        return None
    if not CONFIG.certfile or not CONFIG.keyfile:
        raise RuntimeError("TLS enabled but certificate/key not configured")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CONFIG.certfile, CONFIG.keyfile)
    return context


def _send(conn, code, label, request_id, payload):
    conn.settimeout(CONFIG.write_timeout)
    conn.sendall(build_response(code, label, request_id, payload))


def handle_client(raw_conn, address, context=None):
    session = Session()
    conn = raw_conn
    auth_deadline = time.monotonic() + CONFIG.auth_timeout
    failures = 0
    window_start = time.monotonic()
    window_requests = 0
    try:
        conn.settimeout(CONFIG.auth_timeout)
        if CONFIG.use_tls:
            context = context or _tls_context()
            conn = context.wrap_socket(raw_conn, server_side=True, do_handshake_on_connect=False)
            conn.do_handshake()
        logger.info("event=TCP_CONNECTED ip=%s", address[0])
        for _ in range(CONFIG.max_requests_per_connection):
            request = None
            rid = str(uuid.uuid4())
            try:
                now = time.monotonic()
                deadline = now + CONFIG.message_timeout
                if not session.authenticated:
                    deadline = min(deadline, auth_deadline)
                else:
                    deadline = min(deadline, now + CONFIG.idle_timeout)
                request = read_message(conn, CONFIG.max_message_size, deadline)
                rid = request.request_id
                now = time.monotonic()
                if now - window_start >= 1:
                    window_start, window_requests = now, 0
                window_requests += 1
                if window_requests > CONFIG.max_requests_per_second:
                    _send(conn, 400, "BAD_REQUEST", rid, {"message": "Request limit exceeded"})
                    break
                code, label, payload = handle_request(request, session)
                _send(conn, code, label, rid, payload)
            except TimeoutError:
                _send(conn, 408, "TIMEOUT", rid, {"message": "Connection timed out"})
                break
            except VAPError as exc:
                _send(conn, exc.code, exc.label, rid, {"message": str(exc)})
                # Never reuse a stream after a framing failure: unread bytes may
                # otherwise become a different request. No previous request ID.
                if request is None:
                    break
                if request.command == "AUTH" and isinstance(exc, (BadRequest, Unauthorized)):
                    failures += 1
                    if failures >= CONFIG.max_auth_failures:
                        break
            except (ConnectionError, OSError):
                break
            except Exception:
                logger.exception("event=INTERNAL_ERROR ip=%s request_id=%s", address[0], rid)
                _send(conn, 500, "INTERNAL_ERROR", rid, {"message": "Internal server error"})
                break
    except (OSError, ConnectionError):
        # Includes disconnected peers, failed handshakes and failed error writes.
        pass
    finally:
        conn.close()
        if conn is not raw_conn:
            raw_conn.close()
        logger.info("event=TCP_DISCONNECTED ip=%s", address[0])


class ConnectionLimiter:
    def __init__(self, maximum, per_ip):
        self.maximum = maximum
        self.per_ip = per_ip
        self.total = 0
        self.counts = {}
        self.lock = threading.Lock()

    def acquire(self, ip):
        with self.lock:
            count = self.counts.get(ip, 0)
            if self.total >= self.maximum or count >= self.per_ip:
                return False
            self.total += 1
            self.counts[ip] = count + 1
            return True

    def release(self, ip):
        with self.lock:
            self.total -= 1
            count = self.counts[ip] - 1
            if count:
                self.counts[ip] = count
            else:
                del self.counts[ip]


def serve():
    context = _tls_context()  # Fail before listening if TLS cannot initialize.
    limiter = ConnectionLimiter(CONFIG.max_connections, CONFIG.max_connections_per_ip)

    def worker(conn, addr):
        try:
            handle_client(conn, addr, context)
        finally:
            limiter.release(addr[0])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((CONFIG.host, CONFIG.port))
        server.listen(CONFIG.max_connections)
        logger.info("VAP server listening on %s:%s tls=%s", CONFIG.host, CONFIG.port, CONFIG.use_tls)
        while True:
            conn, addr = server.accept()
            if not limiter.acquire(addr[0]):
                conn.close()
                continue
            try:
                threading.Thread(target=worker, args=(conn, addr), daemon=True).start()
            except Exception:
                conn.close()
                limiter.release(addr[0])
                raise


if __name__ == "__main__":
    serve()
