"""Suíte de integração: exige PostgreSQL com as migrations aplicadas.

Roda no job `integracao` da CI (serviço Postgres do GitHub Actions) ou
localmente contra o banco do docker compose:

    DATABASE_URL=postgresql+psycopg://voluntiva_app:voluntiva_app_dev@localhost:5433/voluntiva \
        python -m pytest -m integracao

O backend conecta como voluntiva_app, então estes testes também exercitam
as policies de RLS da migration 0003. Sem banco no ar, todos são pulados.

Cada teste cria os próprios dados com e-mails/nomes únicos: a suíte pode
rodar várias vezes no mesmo banco e convive com o seed de desenvolvimento.
"""
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

SENHA = "senha-de-teste-123"


_PASTA = Path(__file__).parent


def pytest_collection_modifyitems(items):
    # Hook global: marca só os testes desta pasta (não, por exemplo,
    # tests/test_integracao_contratos.py, que roda sem banco).
    for item in items:
        if _PASTA in Path(str(item.fspath)).parents:
            item.add_marker(pytest.mark.integracao)


@pytest.fixture(scope="session")
def banco_disponivel():
    from app.db.session import engine
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1 FROM public.acao_social LIMIT 1"))
    except Exception as exc:  # noqa: BLE001 - qualquer falha = sem banco
        motivo = f"PostgreSQL indisponível para integração: {exc.__class__.__name__}: {exc}"
        # Na CI o banco é obrigatório: pular em silêncio deixaria o job verde
        # sem ter testado nada.
        if os.environ.get("EXIGIR_BANCO") == "1":
            pytest.fail(motivo)
        pytest.skip(motivo)
    return True


@pytest.fixture(scope="session")
def cliente(banco_disponivel):
    from app.main import app
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c


def unico(prefixo: str) -> str:
    return f"{prefixo}-{uuid.uuid4().hex[:10]}"


def entrar(cliente, email: str, senha: str = SENHA) -> dict:
    resposta = cliente.post("/api/v1/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def nova_ong(cliente):
    """Cadastra uma ONG com sede e devolve (ong_id, unidade_id, cabeçalhos)."""
    def criar(causa: str = "educacao"):
        email = f"{unico('ong')}@teste.dev"
        resposta = cliente.post("/api/v1/ongs", json={
            "nome": unico("ONG Teste"), "email": email, "senha": SENHA, "causa": causa,
            "sede": {"nome": "Sede", "cidade": "Belo Horizonte", "uf": "MG"},
        })
        assert resposta.status_code == 201, resposta.text
        cabecalhos = entrar(cliente, email)
        minhas = cliente.get("/api/v1/ongs/minhas", headers=cabecalhos).json()
        assert len(minhas) == 1 and minhas[0]["papel"] == "proprietario"
        return minhas[0]["id"], minhas[0]["unidades"][0]["id"], cabecalhos
    return criar


@pytest.fixture
def novo_voluntario(cliente):
    """Cadastra um voluntário e devolve (email, cabeçalhos)."""
    def criar():
        email = f"{unico('vol')}@teste.dev"
        resposta = cliente.post("/api/v1/auth/registro", json={
            "nome": "Voluntária Teste", "email": email, "senha": SENHA,
        })
        assert resposta.status_code == 201, resposta.text
        return email, entrar(cliente, email)
    return criar
