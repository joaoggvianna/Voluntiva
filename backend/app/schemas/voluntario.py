"""Schemas do perfil do voluntário, habilidades e histórico."""
import datetime as dt
import decimal
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import NivelHabilidade, StatusAcao, StatusInscricao


class HabilidadeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    categoria: str | None


class HabilidadeDoVoluntario(BaseModel):
    habilidade_id: uuid.UUID
    nivel: NivelHabilidade = NivelHabilidade.BASICO


class HabilidadeDoPerfil(HabilidadeDoVoluntario):
    nome: str
    categoria: str | None


class JanelaDisponibilidade(BaseModel):
    """Janela semanal. dia_semana: 0 = domingo ... 6 = sábado."""
    model_config = ConfigDict(from_attributes=True)

    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: dt.time
    hora_fim: dt.time

    @model_validator(mode="after")
    def _ordem(self):
        if self.hora_fim <= self.hora_inicio:
            raise ValueError("hora_fim deve ser posterior a hora_inicio")
        return self


class PerfilVoluntario(BaseModel):
    usuario_id: uuid.UUID
    voluntario_id: uuid.UUID
    nome: str
    email: str
    telefone: str | None
    data_nascimento: dt.date | None
    cidade: str | None
    uf: str | None
    biografia: str | None
    habilidades: list[HabilidadeDoPerfil]
    disponibilidade: list[JanelaDisponibilidade]


class PerfilUpdate(BaseModel):
    """PUT /voluntarios/eu. Campo ausente = não mexer.
    `habilidades` e `disponibilidade`, quando enviadas, substituem a lista inteira."""
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    telefone: str | None = Field(default=None, pattern=r"^[0-9]{10,13}$")
    data_nascimento: dt.date | None = None
    cidade: str | None = Field(default=None, max_length=120)
    uf: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    biografia: str | None = Field(default=None, max_length=1000)
    habilidades: list[HabilidadeDoVoluntario] | None = Field(default=None, max_length=50)
    disponibilidade: list[JanelaDisponibilidade] | None = Field(default=None, max_length=50)

    @field_validator("data_nascimento")
    @classmethod
    def _idade_minima(cls, valor: dt.date | None) -> dt.date | None:
        # Mesma regra da CHECK voluntario_idade_minima_chk (16 anos).
        if valor is None:
            return valor
        hoje = dt.date.today()
        try:
            limite = hoje.replace(year=hoje.year - 16)
        except ValueError:  # 29/02
            limite = hoje.replace(year=hoje.year - 16, day=28)
        if valor > limite:
            raise ValueError("O voluntário precisa ter pelo menos 16 anos")
        return valor

    @model_validator(mode="after")
    def _nome_nao_nulo(self):
        if "nome" in self.model_fields_set and self.nome is None:
            raise ValueError("nome não pode ser vazio")
        return self


class ItemHistorico(BaseModel):
    acao_id: uuid.UUID
    acao_titulo: str
    ong_nome: str
    inicio: dt.datetime
    fim: dt.datetime
    status_acao: StatusAcao
    status_inscricao: StatusInscricao
    check_in: dt.datetime | None
    check_out: dt.datetime | None
    horas_computadas: decimal.Decimal | None


class Historico(BaseModel):
    """GET /voluntarios/eu/historico: ações já encerradas e totais."""
    itens: list[ItemHistorico]
    total_acoes: int
    presencas: int
    ausencias: int
    total_horas: decimal.Decimal
