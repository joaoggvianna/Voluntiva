"""Base declarativa compartilhada por todos os modelos."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Mapeia tabelas já existentes no banco — não gera DDL."""
    pass
