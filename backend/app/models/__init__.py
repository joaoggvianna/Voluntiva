"""Reexporta todos os modelos.

Importar este pacote registra todas as classes no mapper do SQLAlchemy,
o que é necessário para resolver os relationships por string.
"""
from app.models.acao import AcaoHabilidade, AcaoSocial, Habilidade
from app.models.enums import (
    NivelHabilidade,
    PapelMembro,
    StatusAcao,
    StatusInscricao,
    TipoNotificacao,
    TipoUsuario,
)
from app.models.inscricao import Inscricao, Presenca
from app.models.notificacao import Notificacao
from app.models.ong import Ong, OngMembro, Unidade
from app.models.usuario import (
    Usuario,
    Voluntario,
    VoluntarioDisponibilidade,
    VoluntarioHabilidade,
)

__all__ = [
    "AcaoHabilidade", "AcaoSocial", "Habilidade",
    "Inscricao", "Presenca", "Notificacao",
    "Ong", "OngMembro", "Unidade",
    "Usuario", "Voluntario", "VoluntarioDisponibilidade", "VoluntarioHabilidade",
    "NivelHabilidade", "PapelMembro", "StatusAcao", "StatusInscricao",
    "TipoNotificacao", "TipoUsuario",
]
