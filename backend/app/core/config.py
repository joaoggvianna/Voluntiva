"""Configuração da aplicação, carregada de variáveis de ambiente.

Usa pydantic-settings: cada campo é validado no boot, então um .env
malformado falha na subida do processo e não no meio de uma requisição.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Ambiente ----
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False

    # ---- Banco ----
    database_url: str
    test_database_url: str | None = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False

    # ---- JWT ----
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ---- API ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"

    # ---- Protocolo VAP ----
    vap_host: str = "0.0.0.0"
    vap_port: int = 9009
    vap_max_message_bytes: int = 65536
    vap_idle_timeout: int = 120
    vap_max_connections: int = 100

    # ---- Supabase (opcional: Storage / API REST) ----
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    # ---- Argon2id ----
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("jwt_secret")
    @classmethod
    def _segredo_forte(cls, v: str) -> str:
        # Falha cedo e alto: um segredo curto ou o placeholder do .env.example
        # invalida toda a autenticação do sistema.
        if len(v) < 32:
            raise ValueError("JWT_SECRET precisa ter ao menos 32 caracteres")
        if "troque" in v.lower():
            raise ValueError("JWT_SECRET ainda é o placeholder do .env.example")
        return v

    @field_validator("database_url")
    @classmethod
    def _driver_psycopg3(cls, v: str) -> str:
        if not v.startswith("postgresql+psycopg://"):
            raise ValueError(
                "DATABASE_URL deve usar o driver psycopg3: "
                "postgresql+psycopg://usuario:senha@host:5432/postgres"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Cacheado: o .env é lido uma única vez por processo."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
