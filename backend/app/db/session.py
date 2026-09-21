"""Engine e sessão do SQLAlchemy.

IMPORTANTE: este projeto NÃO usa Base.metadata.create_all().
A fonte da verdade do schema é db/migrations/0001_voluntiva_schema.sql,
que contém enums, triggers, views e constraints que o ORM não sabe gerar.
Os modelos apenas mapeiam o que já existe no banco.
"""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine: Engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,   # descarta conexões mortas pelo pooler do Supabase
    pool_recycle=1800,
    echo=settings.db_echo,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


@event.listens_for(engine, "connect")
def _configurar_conexao(dbapi_connection, connection_record) -> None:
    """Timeout de statement: uma query travada não segura a conexão para sempre."""
    with dbapi_connection.cursor() as cur:
        cur.execute("SET statement_timeout = '30s'")
        cur.execute("SET idle_in_transaction_session_timeout = '60s'")


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI. Garante rollback em erro e close sempre."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
