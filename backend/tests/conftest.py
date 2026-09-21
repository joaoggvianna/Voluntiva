"""Fixtures e configuração mínima da suíte.

A suíte roda sem .env e sem banco no ar. Os testes de protocolo
(tests/vap/) usam os mocks de protocol/auth.py e protocol/services.py; os
de criptografia só precisam que as Settings carreguem.

Quem precisar de banco de verdade deve marcar com @pytest.mark.integracao
e usar a fixture `db_url`, que aponta para TEST_DATABASE_URL — nunca para
o Supabase compartilhado da equipe.
"""
import os

import pytest

# Precisa vir ANTES de qualquer import de app.*: app.core.config instancia
# as Settings no import do módulo, e campos obrigatórios sem valor fazem o
# coletor do pytest abortar.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://voluntiva:voluntiva@127.0.0.1:5432/voluntiva_test",
)
os.environ.setdefault(
    "JWT_SECRET",
    "segredo-apenas-para-testes-com-mais-de-32-caracteres",
)
# Argon2 mais leve nos testes: os parâmetros de produção fazem cada hash
# custar ~100ms, o que sozinho multiplicaria o tempo da suíte.
os.environ.setdefault("ARGON2_TIME_COST", "1")
os.environ.setdefault("ARGON2_MEMORY_COST", "8192")
os.environ.setdefault("ARGON2_PARALLELISM", "1")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integracao: exige PostgreSQL no ar (TEST_DATABASE_URL)"
    )


@pytest.fixture(scope="session")
def settings():
    from app.core.config import get_settings
    return get_settings()


@pytest.fixture(scope="session")
def db_url() -> str:
    from app.core.config import get_settings
    cfg = get_settings()
    return cfg.test_database_url or cfg.database_url
