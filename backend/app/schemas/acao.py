"""Schemas de ação social."""
import datetime as dt
import uuid
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings
from app.models.enums import CausaSocial, StatusAcao


def _com_fuso(valor: dt.datetime | None) -> dt.datetime | None:
    """Data/hora sem fuso é interpretada no fuso da aplicação.

    Sem isso, o Postgres a leria no fuso da sessão (UTC no Supabase) e uma
    ação marcada para 14h apareceria às 11h. Também evita comparar datas
    com e sem fuso no PATCH, o que levanta TypeError no Python.
    """
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=ZoneInfo(settings.fuso_horario))
    return valor


class AcaoCreate(BaseModel):
    ong_id: uuid.UUID
    unidade_id: uuid.UUID | None = None
    titulo: str = Field(min_length=3, max_length=160)
    descricao: str | None = Field(default=None, max_length=5000)
    local_texto: str | None = None
    inicio: dt.datetime
    fim: dt.datetime
    vagas: int = Field(ge=1, le=100_000)
    habilidades: list[uuid.UUID] = Field(default_factory=list)
    # Subconjunto (ou acréscimo) de `habilidades` que o voluntário precisa ter.
    habilidades_obrigatorias: list[uuid.UUID] = Field(default_factory=list)
    # Criar já publicada evita o "rascunho órfão" de criar e depois publicar.
    status: Literal[StatusAcao.RASCUNHO, StatusAcao.PUBLICADA] = StatusAcao.RASCUNHO
    # Sem causa, a ação herda a causa da ONG.
    causa: CausaSocial | None = None

    _fuso = field_validator("inicio", "fim")(_com_fuso)

    @model_validator(mode="after")
    def _periodo_valido(self):
        # Mesma regra da CHECK acao_periodo_chk: rejeitar aqui dá erro 422
        # legível em vez de deixar o banco levantar IntegrityError.
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior a inicio")
        return self


class AcaoUpdate(BaseModel):
    """PATCH parcial. Regras que dependem do estado atual da ação
    (transição de status, mínimo de vagas, período combinado com o valor
    já gravado) ficam em acao_service.atualizar."""
    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    descricao: str | None = Field(default=None, max_length=5000)
    local_texto: str | None = None
    inicio: dt.datetime | None = None
    fim: dt.datetime | None = None
    vagas: int | None = Field(default=None, ge=1, le=100_000)
    status: StatusAcao | None = None
    causa: CausaSocial | None = None
    # Enviar null explicitamente desvincula a ação da unidade.
    unidade_id: uuid.UUID | None = None
    # Quando enviada, substitui a lista inteira de habilidades da ação.
    habilidades: list[uuid.UUID] | None = None
    habilidades_obrigatorias: list[uuid.UUID] | None = None

    _fuso = field_validator("inicio", "fim")(_com_fuso)


class AcaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ong_id: uuid.UUID
    unidade_id: uuid.UUID | None
    titulo: str
    descricao: str | None
    local_texto: str | None
    inicio: dt.datetime
    fim: dt.datetime
    vagas: int
    status: StatusAcao
    causa: CausaSocial | None


class HabilidadeDaAcao(BaseModel):
    id: uuid.UUID
    nome: str
    obrigatoria: bool


class AcaoComVagas(BaseModel):
    """Item de GET /acoes e corpo de GET /acoes/{id}: a ação com ocupação
    (view vw_acao_vagas), unidade e habilidades pedidas."""
    acao_id: uuid.UUID
    # `codigo` é o identificador inteiro público, usado como action_id
    # no protocolo VAP. Ver db/migrations/0002.
    codigo: int
    ong_id: uuid.UUID
    ong_nome: str
    unidade_id: uuid.UUID | None
    unidade_nome: str | None
    unidade_cidade: str | None
    unidade_uf: str | None
    titulo: str
    descricao: str | None
    local_texto: str | None
    inicio: dt.datetime
    fim: dt.datetime
    status: StatusAcao
    causa: CausaSocial | None
    vagas: int
    vagas_ocupadas: int
    vagas_disponiveis: int
    em_lista_espera: int
    habilidades: list[HabilidadeDaAcao]
