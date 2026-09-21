"""Schemas de inscrição e presença."""
import datetime as dt
import decimal
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusInscricao


class InscricaoCreate(BaseModel):
    acao_id: uuid.UUID


class InscricaoCancel(BaseModel):
    motivo: str | None = None


class InscricaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    acao_id: uuid.UUID
    voluntario_id: uuid.UUID
    status: StatusInscricao
    inscrito_em: dt.datetime
    cancelado_em: dt.datetime | None


class PresencaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inscricao_id: uuid.UUID
    check_in: dt.datetime
    check_out: dt.datetime | None
    horas_computadas: decimal.Decimal | None
