"""Comandos de gestão do VAP: validação no handler (mocks) e tradução
de vocabulário no adapter real (services_db), sem banco."""
import uuid
from types import SimpleNamespace

import pytest

from protocol import services as mock
from protocol import services_db
from protocol.errors import BadRequest, Conflict, Forbidden, NotFound
from protocol.handlers import handle_request
from protocol.models import Request, Session


def req(command, payload=None):
    return Request(command=command, request_id="1", payload=payload or {})


def ong():
    return Session(user_id=str(uuid.uuid4()), role="ONG", authenticated=True)


def voluntario():
    return Session(user_id=str(uuid.uuid4()), role="VOLUNTEER", authenticated=True)


NOVA = {
    "title": "Mutirão na praça",
    "starts_at": "2030-05-10T09:00:00-03:00",
    "ends_at": "2030-05-10T12:00:00-03:00",
    "capacity": 5,
}


@pytest.fixture(autouse=True)
def limpar_mock():
    acoes = {k: v.copy() for k, v in mock.ACTIONS.items()}
    yield
    mock.ACTIONS.clear()
    mock.ACTIONS.update(acoes)
    mock.ATTENDANCE.clear()
    mock.NOTIFICATIONS.clear()


# ---------------- Handler: papel e forma do payload ----------------

def test_voluntario_nao_cria_acao():
    with pytest.raises(Forbidden):
        handle_request(req("CREATE_ACTION", NOVA), voluntario())


def test_ong_cria_acao_publicada():
    code, label, body = handle_request(req("CREATE_ACTION", {**NOVA, "publish": True}), ong())
    assert (code, label) == (201, "CREATED")
    assert body["status"] == "OPEN"


@pytest.mark.parametrize("payload,erro", [
    ({k: v for k, v in NOVA.items() if k != "title"}, "title is required"),
    ({**NOVA, "capacity": "5"}, "capacity must be int"),
    ({**NOVA, "capacity": True}, "capacity must be int"),
    ({**NOVA, "titel": "x"}, "Unknown field"),
    ({**NOVA, "status": "OPEN"}, "publish"),
    ({**NOVA, "skills": [1]}, "skills must be a list of strings"),
])
def test_criacao_valida_payload(payload, erro):
    with pytest.raises(BadRequest, match=erro):
        handle_request(req("CREATE_ACTION", payload), ong())


def test_edicao_exige_action_id_e_algum_campo():
    with pytest.raises(BadRequest, match="action_id"):
        handle_request(req("UPDATE_ACTION", {"title": "Novo"}), ong())
    with pytest.raises(BadRequest, match="Nothing to update"):
        handle_request(req("UPDATE_ACTION", {"action_id": 1}), ong())


@pytest.mark.parametrize("campo", ["org_id", "publish", "skills"])
def test_edicao_recusa_campos_de_criacao(campo):
    valor = {"org_id": "x", "publish": True, "skills": []}[campo]
    with pytest.raises(BadRequest, match="cannot be changed"):
        handle_request(req("UPDATE_ACTION", {"action_id": 1, campo: valor}), ong())


def test_edicao_recusa_status_desconhecido():
    with pytest.raises(BadRequest, match="Invalid status"):
        handle_request(req("UPDATE_ACTION", {"action_id": 1, "status": "DRAFT"}), ong())


def test_cancelar_acao_pelo_vap():
    code, _, body = handle_request(req("UPDATE_ACTION", {"action_id": 1, "status": "CANCELLED"}), ong())
    assert code == 200 and body["status"] == "CANCELLED"
    with pytest.raises(Conflict):
        handle_request(req("UPDATE_ACTION", {"action_id": 1, "title": "Outro"}), ong())


def test_presenca_completa():
    sessao = ong()
    pedido = {"action_id": 1, "volunteer_email": "ana@exemplo.com"}
    code, _, body = handle_request(req("CHECK_IN", pedido), sessao)
    assert code == 201 and body["check_out"] is None
    code, _, body = handle_request(req("CHECK_OUT", pedido), sessao)
    assert code == 200 and body["hours"] == 2.0
    with pytest.raises(Conflict):
        handle_request(req("CHECK_OUT", pedido), sessao)


def test_check_out_sem_check_in():
    with pytest.raises(NotFound):
        handle_request(req("CHECK_OUT", {"action_id": 1, "volunteer_email": "a@b.com"}), ong())


def test_presenca_exige_email_e_papel():
    with pytest.raises(BadRequest, match="volunteer_email"):
        handle_request(req("CHECK_IN", {"action_id": 1}), ong())
    with pytest.raises(Forbidden):
        handle_request(req("CHECK_IN", {"action_id": 1, "volunteer_email": "a@b.com"}), voluntario())


def test_listar_notificacoes_valida_limite():
    with pytest.raises(BadRequest, match="limit"):
        handle_request(req("LIST_NOTIFICATIONS", {"limit": 0}), voluntario())
    with pytest.raises(BadRequest, match="unread_only"):
        handle_request(req("LIST_NOTIFICATIONS", {"unread_only": "sim"}), voluntario())


def test_listar_notificacoes_do_proprio_usuario():
    sessao = voluntario()
    mock.NOTIFICATIONS[sessao.user_id] = [
        {"id": "1", "title": "A", "read": False}, {"id": "2", "title": "B", "read": True},
    ]
    _, _, body = handle_request(req("LIST_NOTIFICATIONS", {"unread_only": True}), sessao)
    assert body["unread"] == 1 and [n["id"] for n in body["notifications"]] == ["1"]
    _, _, outro = handle_request(req("LIST_NOTIFICATIONS"), voluntario())
    assert outro["notifications"] == []


def test_comandos_de_gestao_exigem_autenticacao():
    from protocol.errors import Unauthorized
    for comando in ("CREATE_ACTION", "UPDATE_ACTION", "CHECK_IN", "CHECK_OUT", "LIST_NOTIFICATIONS"):
        with pytest.raises(Unauthorized):
            handle_request(req(comando, {}), Session())


# ---------------- Adapter real: tradução, sem banco ----------------

def test_datas_sem_fuso_sao_recusadas():
    with pytest.raises(BadRequest, match="timezone"):
        services_db._instante("2030-05-10T09:00:00", "starts_at")


def test_campos_traduzidos_para_o_schema():
    dados = services_db._traduzir_campos({
        "title": "T", "capacity": 3, "location": "Praça",
        "starts_at": "2030-05-10T09:00:00Z", "unit_id": str(uuid.UUID(int=7)),
    })
    assert dados["titulo"] == "T" and dados["vagas"] == 3 and dados["local_texto"] == "Praça"
    assert dados["inicio"].utcoffset().total_seconds() == 0
    assert dados["unidade_id"] == uuid.UUID(int=7)


def test_status_do_protocolo_mapeia_para_o_banco():
    assert services_db._STATUS_BANCO == {
        "DRAFT": "rascunho", "OPEN": "publicada", "IN_PROGRESS": "em_andamento",
        "CLOSED": "concluida", "CANCELLED": "cancelada",
    }


def test_ong_sem_vinculo_e_proibida(monkeypatch):
    monkeypatch.setattr(services_db.permissao, "tem_acesso_ong", lambda *a, **k: False)
    with pytest.raises(Forbidden):
        services_db._exigir_acesso(SimpleNamespace(), str(uuid.uuid4()), "ONG", uuid.uuid4(), None)


def test_voluntario_nunca_passa_no_adapter():
    with pytest.raises(Forbidden):
        services_db._exigir_acesso(SimpleNamespace(), str(uuid.uuid4()), "VOLUNTEER", uuid.uuid4(), None)
