"""Schemas de autenticação."""
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import TipoUsuario


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)


class RegistroVoluntarioRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    telefone: str | None = Field(default=None, pattern=r"^[0-9]{10,13}$")
    cidade: str | None = None
    uf: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")


class UsuarioPublico(BaseModel):
    """Representação segura do usuário: nunca inclui senha_hash."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    email: EmailStr
    tipo: TipoUsuario
    ativo: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UsuarioPublico
