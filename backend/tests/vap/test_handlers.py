import pytest
from protocol.handlers import handle_request
from protocol.models import Request, Session
from protocol.errors import Unauthorized, Forbidden, Conflict

def req(command, payload=None):
    return Request(command=command, request_id="1", payload=payload or {})

def test_ping_works_without_auth():
    session = Session()
    code, label, body = handle_request(req("PING"), session)
    assert code == 200
    assert body["message"] == "PONG"

def test_list_requires_auth():
    session = Session()
    with pytest.raises(Unauthorized):
        handle_request(req("LIST_ACTIONS"), session)

def test_volunteer_can_register():
    session = Session(user_id="v-99", role="VOLUNTEER", authenticated=True)
    code, _, _ = handle_request(req("REGISTER_ACTION", {"action_id": 1}), session)
    assert code == 201

def test_ong_cannot_register():
    session = Session(user_id="o-99", role="ONG", authenticated=True)
    with pytest.raises(Forbidden):
        handle_request(req("REGISTER_ACTION", {"action_id": 1}), session)
