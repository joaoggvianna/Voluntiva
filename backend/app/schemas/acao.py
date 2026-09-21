"""Schemas de ação social."""
import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import StatusAcao


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

    @model_validator(mode="after")
    def _periodo_valido(self):
        # Mesma regra da CHECK acao_periodo_chk: rejeitar aqui dá erro 422
        # legível em vez de deixar o banco levantar IntegrityError.
        if self.fim <= self.inicio:
            raise ValueError("fim deve ser posterior a inicio")
        return self


class AcaoUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=160)
    descricao: str | None = None
    local_texto: str | None = None
    inicio: dt.datetime | None = None
    fim: dt.datetime | None = None
    vagas: int | None = Field(default=None, ge=1)
    status: StatusAcao | None = None


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


class AcaoComVagas(AcaoResponse):
    """Projeção da view vw_acao_vagas."""
    # `codigo` é o identificador inteiro público, usado como action_id
    # no protocolo VAP. Ver db/migrations/0002.
    codigo: int
    ong_nome: str
    vagas_ocupadas: int
    vagas_disponiveis: int
    em_lista_espera: int
