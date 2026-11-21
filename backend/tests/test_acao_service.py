"""Regras de edição de ação (acao_service.atualizar), sem banco."""
import datetime as dt
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.exceptions import ConflitoDeEstado, DadosInvalidos
from app.models import StatusAcao
from app.schemas.acao import AcaoCreate, AcaoUpdate
from app.services import acao_service

UTC = dt.timezone.utc
INICIO = dt.datetime(2026, 12, 5, 14, 0, tzinfo=UTC)
FIM = dt.datetime(2026, 12, 5, 17, 0, tzinfo=UTC)


def acao(status=StatusAcao.PUBLICADA, vagas=10):
    return SimpleNamespace(
        id=uuid.uuid4(), status=status, vagas=vagas, inicio=INICIO, fim=FIM, titulo="Mutirão"
    )


def db_com(acao_obj, confirmadas=0):
    db = Mock()
    db.get.return_value = acao_obj
    db.scalar.return_value = confirmadas
    return db


@pytest.mark.parametrize("atual,novo", [
    (StatusAcao.RASCUNHO, StatusAcao.PUBLICADA),
    (StatusAcao.RASCUNHO, StatusAcao.CANCELADA),
    (StatusAcao.PUBLICADA, StatusAcao.EM_ANDAMENTO),
    (StatusAcao.PUBLICADA, StatusAcao.CANCELADA),
    (StatusAcao.EM_ANDAMENTO, StatusAcao.CONCLUIDA),
    (StatusAcao.PUBLICADA, StatusAcao.PUBLICADA),
])
def test_transicoes_permitidas(atual, novo):
    acao_service.validar_transicao(atual, novo)


@pytest.mark.parametrize("atual,novo", [
    (StatusAcao.PUBLICADA, StatusAcao.RASCUNHO),
    (StatusAcao.RASCUNHO, StatusAcao.CONCLUIDA),
    (StatusAcao.EM_ANDAMENTO, StatusAcao.PUBLICADA),
])
def test_transicoes_proibidas(atual, novo):
    with pytest.raises(ConflitoDeEstado):
        acao_service.validar_transicao(atual, novo)


@pytest.mark.parametrize("final", [StatusAcao.CONCLUIDA, StatusAcao.CANCELADA])
def test_acao_encerrada_nao_pode_ser_editada(final):
    db = db_com(acao(status=final))
    with pytest.raises(ConflitoDeEstado):
        acao_service.atualizar(db, uuid.uuid4(), AcaoUpdate(titulo="Novo título"))
    db.commit.assert_not_called()


def test_concluida_nao_volta_para_publicada():
    db = db_com(acao(status=StatusAcao.CONCLUIDA))
    with pytest.raises(ConflitoDeEstado):
        acao_service.atualizar(db, uuid.uuid4(), AcaoUpdate(status=StatusAcao.PUBLICADA))


def test_nao_reduz_vagas_abaixo_dos_confirmados():
    db = db_com(acao(vagas=10), confirmadas=7)
    with pytest.raises(ConflitoDeEstado):
        acao_service.atualizar(db, uuid.uuid4(), AcaoUpdate(vagas=5))
    db.commit.assert_not_called()


def test_reduz_vagas_ate_os_confirmados():
    alvo = acao(vagas=10)
    db = db_com(alvo, confirmadas=7)
    acao_service.atualizar(db, uuid.uuid4(), AcaoUpdate(vagas=7))
    assert alvo.vagas == 7
    db.commit.assert_called_once()


def test_trava_a_linha_da_acao():
    db = db_com(acao())
    acao_service.atualizar(db, uuid.uuid4(), AcaoUpdate(titulo="Outro título"))
    assert db.get.call_args.kwargs["with_for_update"] is True


def test_fim_antes_do_inicio_gravado_e_rejeitado():
    # Só `fim` muda; a comparação precisa usar o `inicio` já gravado.
    db = db_com(acao())
    with pytest.raises(DadosInvalidos):
        acao_service.atualizar(
            db, uuid.uuid4(), AcaoUpdate(fim=INICIO - dt.timedelta(hours=1))
        )
    db.commit.assert_not_called()


def test_data_sem_fuso_recebe_fuso_da_aplicacao():
    dados = AcaoUpdate(inicio=dt.datetime(2026, 12, 5, 14, 0))
    assert dados.inicio.tzinfo is not None
    # Comparável com datas do banco (com fuso) sem TypeError:
    assert dados.inicio > INICIO


def test_create_sem_fuso_recebe_fuso_da_aplicacao():
    dados = AcaoCreate(
        ong_id=uuid.uuid4(), titulo="Mutirão", vagas=5,
        inicio=dt.datetime(2026, 12, 5, 14, 0), fim=dt.datetime(2026, 12, 5, 17, 0),
    )
    assert dados.inicio.tzinfo is not None
    assert dados.fim.tzinfo is not None


def test_filtro_rf004_usa_coluna_qualificada_da_view():
    # Regressão: na branch original, `ah.acao_id = acao_id` dentro da
    # subconsulta resolvia para ah.acao_id = ah.acao_id (sempre verdadeiro).
    db = Mock()
    db.execute.return_value.mappings.return_value.all.return_value = []
    acao_service.listar_com_vagas(db, voluntario_id=uuid.uuid4())
    sql = str(db.execute.call_args.args[0])
    assert "ah.acao_id = v.acao_id" in sql
    assert "ah.acao_id = acao_id" not in sql
    assert db.execute.call_args.args[1]["fuso"] == "America/Sao_Paulo"
