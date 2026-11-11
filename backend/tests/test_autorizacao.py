"""Regressão: isolamento de ONGs e acesso a unidades."""
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.api.autorizacao import exigir_acesso_ong, exigir_unidade_da_ong
from app.models import TipoUsuario


@pytest.fixture
def ids():
    return [uuid.uuid4() for _ in range(5)]


def usuario(tipo, identificador):
    return SimpleNamespace(tipo=tipo, id=identificador)


def db_com_vinculos(vinculos):
    db = Mock()
    db.scalars.return_value.all.return_value = vinculos
    return db


def test_admin_tem_acesso_sem_vinculo(ids):
    db = db_com_vinculos([])
    exigir_acesso_ong(db, usuario(TipoUsuario.ADMIN, ids[0]), ids[1])
    db.scalars.assert_not_called()


def test_voluntario_nao_pode_gerir_ong(ids):
    with pytest.raises(HTTPException) as erro:
        exigir_acesso_ong(db_com_vinculos([]), usuario(TipoUsuario.VOLUNTARIO, ids[0]), ids[1])
    assert erro.value.status_code == 403


def test_ong_sem_vinculo_nao_pode_operar(ids):
    with pytest.raises(HTTPException) as erro:
        exigir_acesso_ong(db_com_vinculos([]), usuario(TipoUsuario.ONG, ids[0]), ids[1])
    assert erro.value.status_code == 403


def test_membro_ong_inteira_pode_operar(ids):
    vinculo = SimpleNamespace(unidade_id=None)
    exigir_acesso_ong(db_com_vinculos([vinculo]), usuario(TipoUsuario.ONG, ids[0]), ids[1], ids[2])


def test_membro_unidade_nao_pode_operar_outra_unidade(ids):
    vinculo = SimpleNamespace(unidade_id=ids[2])
    with pytest.raises(HTTPException) as erro:
        exigir_acesso_ong(db_com_vinculos([vinculo]), usuario(TipoUsuario.ONG, ids[0]), ids[1], ids[3])
    assert erro.value.status_code == 403


def test_membro_unidade_pode_operar_a_propria(ids):
    vinculo = SimpleNamespace(unidade_id=ids[2])
    exigir_acesso_ong(db_com_vinculos([vinculo]), usuario(TipoUsuario.ONG, ids[0]), ids[1], ids[2])


def test_unidade_de_outra_ong_rejeitada(ids):
    db = Mock()
    db.get.return_value = SimpleNamespace(ong_id=ids[3], ativo=True)
    with pytest.raises(HTTPException) as erro:
        exigir_unidade_da_ong(db, ids[1], ids[2])
    assert erro.value.status_code == 422


def test_unidade_inativa_rejeitada(ids):
    db = Mock()
    db.get.return_value = SimpleNamespace(ong_id=ids[1], ativo=False)
    with pytest.raises(HTTPException) as erro:
        exigir_unidade_da_ong(db, ids[1], ids[2])
    assert erro.value.status_code == 422
