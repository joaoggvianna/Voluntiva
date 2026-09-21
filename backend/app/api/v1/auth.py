"""Rotas de autenticação."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import usuario_atual
from app.core.exceptions import CredenciaisInvalidas, DadosInvalidos, UsuarioInativo
from app.db.session import get_db
from app.models import Usuario
from app.schemas.auth import (
    LoginRequest,
    RegistroVoluntarioRequest,
    TokenResponse,
    UsuarioPublico,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["autenticação"])


@router.post("/registro", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registrar(dados: RegistroVoluntarioRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.registrar_voluntario(db, dados)
    except DadosInvalidos as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.mensagem)


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    try:
        usuario = auth_service.autenticar(db, dados.email, dados.senha)
    except CredenciaisInvalidas as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, exc.mensagem)
    except UsuarioInativo as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, exc.mensagem)
    return auth_service.emitir_tokens(usuario)


@router.get("/eu", response_model=UsuarioPublico)
def eu(usuario: Usuario = Depends(usuario_atual)):
    return usuario
