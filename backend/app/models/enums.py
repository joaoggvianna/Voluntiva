"""Enums Python espelhando os tipos ENUM criados na migration.

Os valores DEVEM bater exatamente com os do banco. Se um enum mudar no
SQL, mude aqui também — não existe geração automática.
"""
from enum import Enum


class TipoUsuario(str, Enum):
    VOLUNTARIO = "voluntario"
    ONG = "ong"
    ADMIN = "admin"


class PapelMembro(str, Enum):
    PROPRIETARIO = "proprietario"
    GESTOR = "gestor"
    OPERADOR = "operador"


class NivelHabilidade(str, Enum):
    BASICO = "basico"
    INTERMEDIARIO = "intermediario"
    AVANCADO = "avancado"


class StatusAcao(str, Enum):
    RASCUNHO = "rascunho"
    PUBLICADA = "publicada"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class StatusInscricao(str, Enum):
    PENDENTE = "pendente"
    CONFIRMADA = "confirmada"
    LISTA_ESPERA = "lista_espera"
    CANCELADA = "cancelada"


class TipoNotificacao(str, Enum):
    ACAO_CRIADA = "acao_criada"
    ACAO_ATUALIZADA = "acao_atualizada"
    ACAO_CANCELADA = "acao_cancelada"
    INSCRICAO_CONFIRMADA = "inscricao_confirmada"
    INSCRICAO_CANCELADA = "inscricao_cancelada"
    LEMBRETE = "lembrete"
