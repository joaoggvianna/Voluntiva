"""Schemas de inscrição e presença."""
import datetime as dt
import decimal
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import CausaSocial, StatusAcao, StatusInscricao


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


class AcaoResumo(BaseModel):
    id: uuid.UUID
    codigo: int
    titulo: str
    inicio: dt.datetime
    fim: dt.datetime
    status: StatusAcao
    causa: CausaSocial | None
    local_texto: str | None
    ong_id: uuid.UUID
    ong_nome: str
    unidade_cidade: str | None
    unidade_uf: str | None


class InscricaoComAcao(InscricaoResponse):
    """GET /inscricoes/minhas: a inscrição com a ação e a presença."""
    acao: AcaoResumo
    check_in: dt.datetime | None
    check_out: dt.datetime | None
    horas_computadas: decimal.Decimal | None


class InscritoResponse(BaseModel):
    """GET /acoes/{id}/inscricoes: visão da ONG sobre cada inscrito."""
    inscricao_id: uuid.UUID
    status: StatusInscricao
    inscrito_em: dt.datetime
    voluntario_id: uuid.UUID
    nome: str
    email: str
    telefone: str | None
    check_in: dt.datetime | None
    check_out: dt.datetime | None
    horas_computadas: decimal.Decimal | None
