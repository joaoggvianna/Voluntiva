"""Lista de espera (inscricao_service), sem banco."""
import datetime as dt
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.core.exceptions import ConflitoDeEstado
from app.models import StatusAcao, StatusInscricao
from app.services import inscricao_service, notificacao_service

FUTURO = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=3)


def acao(status=StatusAcao.PUBLICADA, vagas=1):
    return SimpleNamespace(
        id=uuid.uuid4(), ong_id=uuid.uuid4(), unidade_id=None, titulo="Oficina",
        status=status, vagas=vagas, inicio=FUTURO, fim=FUTURO + dt.timedelta(hours=2),
    )


def banco(acao_obj, *, existente=None, confirmadas=0):
    db = Mock()
    db.info = {}
    voluntario = SimpleNamespace(id=uuid.uuid4())
    db.scalar.side_effect = [voluntario, existente, confirmadas, "Ana"]
    db.get.return_value = acao_obj
    db.execute.return_value.mappings.return_value.all.return_value = []
    return db


def test_lotada_sem_pedir_espera_tenta_confirmar(monkeypatch):
    db = banco(acao(), confirmadas=1)
    monkeypatch.setattr(inscricao_service, "_nome_do_usuario", lambda *_: "Ana")
    inscricao_service.inscrever(db, uuid.uuid4(), uuid.uuid4())
    # Sem lista_espera, quem decide é o trigger (o flush levanta "lotada").
    assert db.add.call_args.args[0].status == StatusInscricao.CONFIRMADA


def test_lotada_com_espera_entra_na_fila(monkeypatch):
    db = banco(acao(), confirmadas=1)
    monkeypatch.setattr(inscricao_service, "_nome_do_usuario", lambda *_: "Ana")
    inscricao_service.inscrever(db, uuid.uuid4(), uuid.uuid4(), lista_espera=True)
    assert db.add.call_args.args[0].status == StatusInscricao.LISTA_ESPERA
    # A ação foi travada antes de contar as vagas.
    assert db.get.call_args.kwargs["with_for_update"] is True


def test_com_vaga_e_espera_confirma_direto(monkeypatch):
    db = banco(acao(vagas=2), confirmadas=1)
    monkeypatch.setattr(inscricao_service, "_nome_do_usuario", lambda *_: "Ana")
    inscricao_service.inscrever(db, uuid.uuid4(), uuid.uuid4(), lista_espera=True)
    assert db.add.call_args.args[0].status == StatusInscricao.CONFIRMADA


@pytest.mark.parametrize("status", [StatusAcao.RASCUNHO, StatusAcao.CANCELADA, StatusAcao.CONCLUIDA])
def test_acao_fora_de_inscricao(status):
    db = banco(acao(status=status))
    with pytest.raises(ConflitoDeEstado):
        inscricao_service.inscrever(db, uuid.uuid4(), uuid.uuid4())
    db.add.assert_not_called()


def test_ja_na_fila_nao_entra_de_novo():
    db = banco(acao(), existente=SimpleNamespace(status=StatusInscricao.LISTA_ESPERA))
    with pytest.raises(ConflitoDeEstado, match="lista de espera"):
        inscricao_service.inscrever(db, uuid.uuid4(), uuid.uuid4(), lista_espera=True)


def test_promocao_confirma_os_primeiros_e_avisa(monkeypatch):
    alvo = acao(vagas=3)
    fila = [
        SimpleNamespace(voluntario_id=uuid.uuid4(), status=StatusInscricao.LISTA_ESPERA)
        for _ in range(2)
    ]
    db = Mock()
    db.scalar.return_value = 1  # 1 confirmada -> 2 vagas livres
    db.scalars.return_value.all.return_value = fila
    db.execute.return_value.all.return_value = [(f.voluntario_id, uuid.uuid4()) for f in fila]
    avisados = []
    monkeypatch.setattr(
        notificacao_service, "notificar_usuario",
        lambda _db, usuario_id, *a, **k: avisados.append(usuario_id),
    )
    promovidas = inscricao_service.promover_lista_espera(db, alvo)
    assert promovidas == fila
    assert all(f.status == StatusInscricao.CONFIRMADA for f in fila)
    assert len(avisados) == 2
    consulta = str(db.scalars.call_args.args[0])
    assert "ORDER BY inscricao.inscrito_em, inscricao.id" in consulta


def test_sem_vaga_livre_ninguem_e_promovido():
    db = Mock()
    db.scalar.return_value = 3
    assert inscricao_service.promover_lista_espera(db, acao(vagas=3)) == []
    db.scalars.assert_not_called()


def test_cancelar_confirmada_promove_a_fila(monkeypatch):
    alvo = acao()
    inscricao = SimpleNamespace(status=StatusInscricao.CONFIRMADA)
    db = Mock()
    db.info = {}
    db.scalar.side_effect = [SimpleNamespace(id=uuid.uuid4()), inscricao]
    db.get.return_value = alvo
    monkeypatch.setattr(inscricao_service, "_nome_do_usuario", lambda *_: "Ana")
    monkeypatch.setattr(notificacao_service, "notificar_gestores", lambda *a, **k: [])
    chamadas = []
    monkeypatch.setattr(inscricao_service, "promover_lista_espera", lambda _db, a: chamadas.append(a))
    inscricao_service.cancelar(db, uuid.uuid4(), alvo.id)
    assert chamadas == [alvo]
    assert inscricao.status == StatusInscricao.CANCELADA


def test_cancelar_quem_estava_na_fila_nao_promove(monkeypatch):
    inscricao = SimpleNamespace(status=StatusInscricao.LISTA_ESPERA)
    db = Mock()
    db.info = {}
    db.scalar.side_effect = [SimpleNamespace(id=uuid.uuid4()), inscricao]
    db.get.return_value = acao()
    monkeypatch.setattr(inscricao_service, "_nome_do_usuario", lambda *_: "Ana")
    monkeypatch.setattr(notificacao_service, "notificar_gestores", lambda *a, **k: [])
    chamadas = []
    monkeypatch.setattr(inscricao_service, "promover_lista_espera", lambda _db, a: chamadas.append(a))
    inscricao_service.cancelar(db, uuid.uuid4(), uuid.uuid4())
    assert chamadas == []
