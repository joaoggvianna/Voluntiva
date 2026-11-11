"""Contratos básicos exigidos pelo frontend integrado."""
import inspect

from app.api.v1 import acoes, auth, inscricoes, ongs


def test_endpoints_necessarios_existem():
    rotas = {
        (rota.path, metodo)
        for modulo in (acoes, auth, inscricoes, ongs)
        for rota in modulo.router.routes
        for metodo in (rota.methods or [])
    }
    for item in (
        ("/auth/registro", "POST"), ("/auth/login", "POST"),
        ("/auth/eu", "GET"), ("/acoes", "GET"),
        ("/acoes/{acao_id}", "GET"), ("/acoes", "POST"),
        ("/acoes/{acao_id}", "PATCH"), ("/inscricoes", "POST"),
        ("/inscricoes/minhas", "GET"), ("/inscricoes/{acao_id}", "DELETE"),
        ("/ongs/minhas", "GET"),
    ):
        assert item in rotas, f"Endpoint ausente: {item}"


def test_listar_inscricoes_requer_usuario_atual():
    assert "usuario" in inspect.signature(inscricoes.minhas).parameters
