"""Services da Fase 1 sem banco: notificações, ONGs, perfil, inscrição."""
import asyncio
import datetime as dt
import decimal
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import BackgroundTasks

from app.core.exceptions import ConflitoDeEstado, DadosInvalidos, RecursoNaoEncontrado
from app.models import PapelMembro, StatusAcao, StatusInscricao, TipoUsuario
from app.realtime import entrega
from app.schemas.voluntario import HabilidadeDoVoluntario, PerfilUpdate
from app.services import (
    inscricao_service,
    notificacao_service,
    ong_service,
    voluntario_service,
)

AGORA = dt.datetime(2026, 12, 5, 17, 0, tzinfo=dt.timezone.utc)


def acao(**extra):
    base = dict(
        id=uuid.uuid4(), ong_id=uuid.uuid4(), unidade_id=None, titulo="Mutirão",
        inicio=AGORA, fim=AGORA + dt.timedelta(hours=3), status=StatusAcao.PUBLICADA,
    )
    base.update(extra)
    return SimpleNamespace(**base)


def db_que_retorna(linhas):
    db = Mock()
    db.info = {}
    db.execute.return_value.mappings.return_value.all.return_value = linhas
    return db


# ---------------------------------------------------------------------
# Notificações
# ---------------------------------------------------------------------

def test_notificacao_vai_para_pendentes_da_sessao():
    linha = {"id": uuid.uuid4(), "usuario_id": uuid.uuid4()}
    db = db_que_retorna([linha])
    notificacao_service.notificar_inscritos(db, acao(), Mock(value="acao_cancelada"), "T", "M")
    assert db.info[notificacao_service.PENDENTES] == [linha]


def test_notificacao_e_um_insert_select_unico():
    db = db_que_retorna([])
    notificacao_service.notificar_inscritos(db, acao(), Mock(value="acao_cancelada"), "T", "M")
    assert db.execute.call_count == 1
    sql = str(db.execute.call_args.args[0])
    assert "INSERT INTO public.notificacao" in sql and "SELECT" in sql


def test_compativeis_usa_regra_rf004_sobre_a_acao():
    db = db_que_retorna([])
    notificacao_service.notificar_compativeis(db, acao(), "ONG X")
    sql = str(db.execute.call_args.args[0])
    assert "ah.acao_id = a.id" in sql
    assert "vd.voluntario_id = v.id" in sql


def test_horario_formatado_no_fuso_da_aplicacao():
    # 17h UTC = 14h em São Paulo
    assert notificacao_service.formatar_quando(AGORA) == "05/12/2026 às 14:00"


def test_marcar_lida_de_outra_pessoa_e_404():
    db = Mock()
    db.get.return_value = SimpleNamespace(usuario_id=uuid.uuid4(), lida=False)
    with pytest.raises(RecursoNaoEncontrado):
        notificacao_service.marcar_lida(db, uuid.uuid4(), uuid.uuid4())
    db.commit.assert_not_called()


def test_entrega_agenda_e_envia_pelo_websocket(monkeypatch):
    destino = uuid.uuid4()
    linha = {
        "id": uuid.uuid4(), "usuario_id": destino, "acao_id": None, "tipo": "lembrete",
        "titulo": "Oi", "mensagem": "Teste", "lida": False, "criada_em": AGORA,
    }
    db = SimpleNamespace(info={notificacao_service.PENDENTES: [linha]})
    tarefas = BackgroundTasks()
    assert entrega.agendar_entrega(db, tarefas) == 1
    assert notificacao_service.PENDENTES not in db.info

    enviar = AsyncMock()
    monkeypatch.setattr(entrega.gerenciador, "enviar_para", enviar)
    asyncio.run(entrega.entregar([linha]))
    usuario_id, mensagem = enviar.call_args.args
    assert usuario_id == destino
    assert mensagem["titulo"] == "Oi" and mensagem["criada_em"].startswith("2026-12-05")


# ---------------------------------------------------------------------
# ONGs
# ---------------------------------------------------------------------

def test_minhas_ongs_sem_n_mais_1():
    ong_a, ong_b = uuid.uuid4(), uuid.uuid4()
    unidade = uuid.uuid4()
    vinculos = [
        SimpleNamespace(ong_id=ong_a, unidade_id=None, papel=PapelMembro.OPERADOR),
        SimpleNamespace(ong_id=ong_a, unidade_id=None, papel=PapelMembro.GESTOR),
        SimpleNamespace(ong_id=ong_b, unidade_id=unidade, papel=PapelMembro.OPERADOR),
    ]
    ongs = [SimpleNamespace(id=ong_a, nome="A"), SimpleNamespace(id=ong_b, nome="B")]
    unidades = [
        SimpleNamespace(id=uuid.uuid4(), ong_id=ong_a, nome="Sede", cidade="BH", uf="MG"),
        SimpleNamespace(id=unidade, ong_id=ong_b, nome="Norte", cidade="BH", uf="MG"),
        SimpleNamespace(id=uuid.uuid4(), ong_id=ong_b, nome="Sul", cidade="BH", uf="MG"),
    ]
    db = Mock()
    db.scalars.return_value.all.side_effect = [vinculos, ongs, unidades]
    usuario = SimpleNamespace(id=uuid.uuid4(), tipo=TipoUsuario.ONG)

    resultado = ong_service.minhas(db, usuario)

    assert db.scalars.call_count == 3
    a, b = resultado
    assert a["acesso_total"] and a["papel"] == "gestor" and len(a["unidades"]) == 1
    assert not b["acesso_total"] and [u["nome"] for u in b["unidades"]] == ["Norte"]


def test_unidade_com_acoes_nao_e_removida():
    db = Mock()
    db.get.return_value = SimpleNamespace(ong_id=uuid.UUID(int=1), ativo=True)
    db.scalar.return_value = 2
    with pytest.raises(ConflitoDeEstado):
        ong_service.remover_unidade(db, uuid.UUID(int=1), uuid.uuid4())
    db.delete.assert_not_called()


def test_unidade_de_outra_ong_e_404():
    db = Mock()
    db.get.return_value = SimpleNamespace(ong_id=uuid.uuid4(), ativo=True)
    with pytest.raises(RecursoNaoEncontrado):
        ong_service.obter_unidade(db, uuid.uuid4(), uuid.uuid4())


def test_cadastro_de_ong_com_email_repetido():
    db = Mock()
    db.scalar.return_value = uuid.uuid4()
    from app.schemas.ong import OngCadastro
    dados = OngCadastro(nome="ONG", email="a@exemplo.com", senha="12345678")
    with pytest.raises(DadosInvalidos):
        ong_service.cadastrar(db, dados)
    db.add_all.assert_not_called()


# ---------------------------------------------------------------------
# Perfil e histórico
# ---------------------------------------------------------------------

def test_perfil_recusa_habilidade_inexistente():
    db = Mock()
    db.scalar.side_effect = [SimpleNamespace(id=uuid.uuid4()), 0]
    usuario = SimpleNamespace(id=uuid.uuid4(), nome="Ana")
    dados = PerfilUpdate(habilidades=[HabilidadeDoVoluntario(habilidade_id=uuid.uuid4())])
    with pytest.raises(DadosInvalidos):
        voluntario_service.atualizar_perfil(db, usuario, dados)
    db.commit.assert_not_called()


def test_historico_soma_horas_e_conta_ausencias():
    def item(horas, presente=True):
        return {
            "acao_id": uuid.uuid4(), "acao_titulo": "A", "ong_nome": "O",
            "inicio": AGORA, "fim": AGORA, "status_acao": "concluida",
            "status_inscricao": "confirmada",
            "check_in": AGORA if presente else None, "check_out": AGORA if presente else None,
            "horas_computadas": decimal.Decimal(horas) if presente else None,
        }
    db = db_que_retorna([item("2.5"), item("1.25"), item("0", presente=False)])
    db.scalar.return_value = SimpleNamespace(id=uuid.uuid4())
    resultado = voluntario_service.historico(db, SimpleNamespace(id=uuid.uuid4()))
    assert resultado["total_acoes"] == 3
    assert resultado["presencas"] == 2 and resultado["ausencias"] == 1
    assert resultado["total_horas"] == decimal.Decimal("3.75")


# ---------------------------------------------------------------------
# Inscrição
# ---------------------------------------------------------------------

def test_nao_cancela_inscricao_de_acao_encerrada():
    db = Mock()
    db.scalar.side_effect = [
        SimpleNamespace(id=uuid.uuid4()),
        SimpleNamespace(status=StatusInscricao.CONFIRMADA),
    ]
    db.get.return_value = acao(status=StatusAcao.CONCLUIDA)
    with pytest.raises(ConflitoDeEstado):
        inscricao_service.cancelar(db, uuid.uuid4(), uuid.uuid4())
    db.commit.assert_not_called()


def test_check_in_antes_do_dia_da_acao_e_recusado():
    futura = acao(inicio=dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=3))
    db = Mock()
    db.get.side_effect = [None, SimpleNamespace(acao_id=futura.id), futura]
    with pytest.raises(ConflitoDeEstado):
        inscricao_service.check_in(db, uuid.uuid4(), uuid.uuid4())
    db.add.assert_not_called()
