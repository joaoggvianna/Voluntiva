"""Sobe o servidor VAP com os adapters reais.

    python -m protocol

Sem este wiring, `python -m protocol.server` roda com os mocks de
auth.py e services.py — útil para testar o protocolo isolado, inútil
contra o banco real.
"""
import logging

from . import auth_db, handlers, services_db
from .server import serve

logger = logging.getLogger("vap")

# Troca os mocks pelas implementações ligadas ao PostgreSQL.
handlers.set_auth(auth_db)
handlers.set_services(services_db)

if __name__ == "__main__":
    logger.info("Adapters reais ativos: auth_db + services_db")
    serve()
