"""Regras de autenticação, compartilhadas entre a API REST e o comando LOGIN do VAP."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import CredenciaisInvalidas, DadosInvalidos, UsuarioInativo
from app.core.security import (
    criar_access_token,
    criar_refresh_token,
    hash_senha,
    precisa_rehash,
    verificar_senha,
)
from app.models import TipoUsuario, Usuario, Voluntario
from app.schemas.auth import RegistroVoluntarioRequest


def autenticar(db: Session, email: str, senha: str) -> Usuario:
    """Valida credenciais e devolve o usuário.

    Mesma mensagem de erro para e-mail inexistente e senha errada: revelar
    qual dos dois falhou permite enumerar contas cadastradas.
    """
    usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    if usuario is None:
        # Gasta o mesmo tempo de um verify real para não vazar a
        # existência da conta pelo tempo de resposta.
        hash_senha(senha)
        raise CredenciaisInvalidas("E-mail ou senha incorretos")

    if not verificar_senha(senha, usuario.senha_hash):
        raise CredenciaisInvalidas("E-mail ou senha incorretos")

    if not usuario.ativo:
        raise UsuarioInativo("Conta desativada")

    # Reforça o hash se os parâmetros do Argon2 mudaram desde o cadastro.
    if precisa_rehash(usuario.senha_hash):
        usuario.senha_hash = hash_senha(senha)

    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    return usuario


def emitir_tokens(usuario: Usuario) -> dict:
    return {
        "access_token": criar_access_token(usuario.id, usuario.tipo.value),
        "refresh_token": criar_refresh_token(usuario.id),
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "usuario": usuario,
    }


def registrar_voluntario(db: Session, dados: RegistroVoluntarioRequest) -> Usuario:
    existente = db.scalar(
        select(Usuario).where(func.lower(Usuario.email) == dados.email.lower())
    )
    if existente is not None:
        raise DadosInvalidos("Já existe uma conta com este e-mail")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(dados.senha),
        tipo=TipoUsuario.VOLUNTARIO,
    )
    db.add(usuario)
    db.flush()  # garante o id antes de criar o perfil

    db.add(Voluntario(
        usuario_id=usuario.id,
        telefone=dados.telefone,
        cidade=dados.cidade,
        uf=dados.uf,
    ))
    db.commit()
    db.refresh(usuario)
    return usuario
