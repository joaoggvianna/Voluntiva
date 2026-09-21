"""Testes de hash de senha e JWT."""
import uuid

import jwt
import pytest

from app.core.security import (
    criar_access_token,
    criar_refresh_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)


def test_hash_nao_guarda_senha_em_claro():
    h = hash_senha("senha-secreta-123")
    assert "senha-secreta-123" not in h
    assert h.startswith("$argon2id$")


def test_hash_satisfaz_constraint_do_banco():
    """usuario_senha_hash_chk exige começar com '$' e ter >= 20 caracteres."""
    h = hash_senha("qualquer-senha")
    assert h.startswith("$")
    assert len(h) >= 20


def test_hashes_diferentes_para_mesma_senha():
    """Salt aleatório: dois hashes da mesma senha não podem coincidir."""
    assert hash_senha("igual") != hash_senha("igual")


def test_verificacao_de_senha():
    h = hash_senha("correta")
    assert verificar_senha("correta", h) is True
    assert verificar_senha("errada", h) is False


def test_verificar_senha_nao_levanta_em_hash_invalido():
    assert verificar_senha("x", "nao-e-um-hash") is False


def test_access_token_ida_e_volta():
    uid = uuid.uuid4()
    payload = decodificar_token(criar_access_token(uid, "voluntario"))
    assert payload["sub"] == str(uid)
    assert payload["tipo"] == "voluntario"


def test_refresh_token_nao_serve_como_access():
    """Trocar o scope é a falha que permite escalar um refresh em access."""
    token = criar_refresh_token(uuid.uuid4())
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(token, scope_esperado="access")


def test_token_com_assinatura_adulterada_e_rejeitado():
    token = criar_access_token(uuid.uuid4(), "voluntario")
    adulterado = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(adulterado)
