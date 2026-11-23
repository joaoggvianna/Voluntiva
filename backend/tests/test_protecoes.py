"""Proteções da revisão de segurança: limite de login, cabeçalhos e
autenticação do WebSocket. Sem banco (Mock e monkeypatch)."""
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from app.api.v1 import ws as ws_rota
from app.core.exceptions import CredenciaisInvalidas, MuitasTentativas
from app.core.limites import LimiteTentativas
from app.core.security import criar_access_token, criar_refresh_token, hash_senha
from app.db.session import get_db
from app.main import app
from app.services import auth_service

# ---------------------------------------------------------------------
# LimiteTentativas
# ---------------------------------------------------------------------


def test_limite_bloqueia_apos_maximo_e_libera_depois_da_janela():
    agora = [0.0]
    limite = LimiteTentativas(3, 60, relogio=lambda: agora[0])
    for _ in range(3):
        assert not limite.bloqueado("a@x.com")
        limite.registrar_falha("a@x.com")
    assert limite.bloqueado("a@x.com")
    assert not limite.bloqueado("b@x.com")
    agora[0] = 61
    assert not limite.bloqueado("a@x.com")


def test_limite_zera_apos_sucesso():
    limite = LimiteTentativas(2, 60)
    limite.registrar_falha("a@x.com")
    limite.limpar("a@x.com")
    limite.registrar_falha("a@x.com")
    assert not limite.bloqueado("a@x.com")


@pytest.fixture
def limite_curto(monkeypatch):
    limite = LimiteTentativas(2, 60)
    monkeypatch.setattr(auth_service, "_limite_login", limite)
    return limite


def test_login_bloqueia_por_email_mesmo_inexistente(limite_curto):
    db = Mock()
    db.scalar.return_value = None
    for _ in range(2):
        with pytest.raises(CredenciaisInvalidas):
            auth_service.autenticar(db, "Fulana@Exemplo.com", "senha-errada")
    # Bloqueio vale sem diferenciar maiúsculas e sem consultar o banco.
    db.scalar.reset_mock()
    with pytest.raises(MuitasTentativas):
        auth_service.autenticar(db, "fulana@exemplo.com", "senha-certa-123")
    db.scalar.assert_not_called()


def test_rota_de_login_responde_429(limite_curto):
    db = Mock()
    db.scalar.return_value = None

    def _db():
        yield db

    app.dependency_overrides[get_db] = _db
    try:
        cliente = TestClient(app)
        corpo = {"email": "fulana@exemplo.com", "senha": "senha-errada"}
        assert cliente.post("/api/v1/auth/login", json=corpo).status_code == 401
        assert cliente.post("/api/v1/auth/login", json=corpo).status_code == 401
        resposta = cliente.post("/api/v1/auth/login", json=corpo)
        assert resposta.status_code == 429
        assert resposta.headers["Retry-After"]
        assert resposta.headers["Cache-Control"] == "no-store"
    finally:
        app.dependency_overrides.clear()


def test_login_correto_nao_conta_falha(limite_curto):
    usuario = SimpleNamespace(
        id=uuid.uuid4(), senha_hash=hash_senha("senha-certa-123"), ativo=True,
        ultimo_login=None,
    )
    db = Mock()
    db.scalar.return_value = usuario
    with pytest.raises(CredenciaisInvalidas):
        auth_service.autenticar(db, "fulana@exemplo.com", "senha-errada")
    assert auth_service.autenticar(db, "fulana@exemplo.com", "senha-certa-123") is usuario
    assert not limite_curto.bloqueado("fulana@exemplo.com")


# ---------------------------------------------------------------------
# Cabeçalhos
# ---------------------------------------------------------------------


def test_cabecalhos_de_seguranca_na_api():
    resposta = TestClient(app).get("/api/v1/rota-que-nao-existe")
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert resposta.headers["Referrer-Policy"] == "no-referrer"


# ---------------------------------------------------------------------
# WebSocket: token na primeira mensagem, conta ativa
# ---------------------------------------------------------------------


@pytest.fixture
def ativos(monkeypatch):
    conjunto: set[uuid.UUID] = set()
    monkeypatch.setattr(ws_rota, "_usuario_ativo", lambda uid: uid in conjunto)
    return conjunto


def test_ws_autentica_pela_primeira_mensagem(ativos):
    usuario_id = uuid.uuid4()
    ativos.add(usuario_id)
    with TestClient(app).websocket_connect("/ws/notificacoes") as conexao:
        conexao.send_text(criar_access_token(usuario_id, "voluntario"))
        conexao.send_text("ping")
        assert conexao.receive_text() == "pong"


@pytest.mark.parametrize("token", [
    "nao-e-um-jwt",
    criar_refresh_token(uuid.uuid4()),
])
def test_ws_recusa_token_invalido(ativos, token):
    with TestClient(app).websocket_connect("/ws/notificacoes") as conexao:
        conexao.send_text(token)
        with pytest.raises(WebSocketDisconnect) as erro:
            conexao.receive_text()
    assert erro.value.code == 1008


def test_ws_recusa_conta_desativada(ativos):
    with TestClient(app).websocket_connect("/ws/notificacoes") as conexao:
        conexao.send_text(criar_access_token(uuid.uuid4(), "voluntario"))
        with pytest.raises(WebSocketDisconnect) as erro:
            conexao.receive_text()
    assert erro.value.code == 1008
