"""Rotas da Fase 1 sem banco: autorização, visibilidade e contratos.

O banco é um Mock injetado por dependency override; as consultas reais
ficam para a suíte de integração (tests/integracao/, exige Postgres).
"""
import datetime as dt
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.core.security import criar_access_token, criar_refresh_token
from app.db.session import get_db
from app.main import app
from app.models import PapelMembro, StatusAcao, TipoUsuario
from app.services import acao_service, auth_service, ong_service

ONG = uuid.uuid4()
UNIDADE_A = uuid.uuid4()
UNIDADE_B = uuid.uuid4()


def usuario(tipo, ativo=True):
    return SimpleNamespace(
        id=uuid.uuid4(), tipo=tipo, ativo=ativo, nome="Fulana", email="fulana@exemplo.com"
    )


def vinculo(unidade_id=None, papel=PapelMembro.OPERADOR):
    return SimpleNamespace(unidade_id=unidade_id, papel=papel, ong_id=ONG)


@pytest.fixture
def db():
    banco = Mock()
    banco.info = {}
    banco.scalars.return_value.all.return_value = []
    return banco


@pytest.fixture
def cliente(db):
    estado = {"usuario": None}

    def _db():
        yield db

    def _atual():
        if estado["usuario"] is None:
            from fastapi import HTTPException
            raise HTTPException(401, "Token inválido ou expirado")
        return estado["usuario"]

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[deps.usuario_atual] = _atual
    app.dependency_overrides[deps.usuario_opcional] = lambda: estado["usuario"]
    c = TestClient(app)
    c.estado = estado
    yield c
    app.dependency_overrides.clear()


def detalhe(status=StatusAcao.PUBLICADA):
    agora = dt.datetime.now(dt.timezone.utc)
    return {
        "acao_id": uuid.uuid4(), "codigo": 1, "ong_id": ONG, "ong_nome": "ONG",
        "unidade_id": None, "unidade_nome": None, "unidade_cidade": None, "unidade_uf": None,
        "titulo": "Mutirão", "descricao": None, "local_texto": None,
        "inicio": agora, "fim": agora + dt.timedelta(hours=2), "status": status.value,
        "causa": None, "vagas": 10, "vagas_ocupadas": 0, "vagas_disponiveis": 10,
        "em_lista_espera": 0, "habilidades": [],
    }


# ---------------------------------------------------------------------
# Ações: rascunho só para a ONG
# ---------------------------------------------------------------------

def test_rascunho_nao_lista_para_anonimo(cliente):
    resposta = cliente.get("/api/v1/acoes", params={"status": "rascunho", "ong_id": str(ONG)})
    assert resposta.status_code == 403


def test_rascunho_lista_para_membro_com_total(cliente, db, monkeypatch):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    db.scalars.return_value.all.return_value = [vinculo(UNIDADE_A)]
    chamada = {}

    def falso_buscar(_db, **kw):
        chamada.update(kw)
        return [detalhe(StatusAcao.RASCUNHO)], 7

    monkeypatch.setattr(acao_service, "buscar", falso_buscar)
    resposta = cliente.get(
        "/api/v1/acoes", params={"todos_status": "true", "ong_id": str(ONG)}
    )
    assert resposta.status_code == 200
    assert resposta.headers["X-Total-Count"] == "7"
    assert chamada["status"] is None


def test_detalhe_de_rascunho_e_404_para_outros(cliente, monkeypatch):
    monkeypatch.setattr(acao_service, "obter_detalhe", lambda *_: detalhe(StatusAcao.RASCUNHO))
    assert cliente.get(f"/api/v1/acoes/{uuid.uuid4()}").status_code == 404


def test_detalhe_publicado_e_publico(cliente, monkeypatch):
    monkeypatch.setattr(acao_service, "obter_detalhe", lambda *_: detalhe())
    resposta = cliente.get(f"/api/v1/acoes/{uuid.uuid4()}")
    assert resposta.status_code == 200
    assert resposta.json()["vagas_disponiveis"] == 10


def test_ong_nao_se_inscreve(cliente):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    resposta = cliente.post("/api/v1/inscricoes", json={"acao_id": str(uuid.uuid4())})
    assert resposta.status_code == 403


def test_inscritos_exigem_acesso_a_acao(cliente, db, monkeypatch):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    acao = SimpleNamespace(ong_id=ONG, unidade_id=UNIDADE_B)
    monkeypatch.setattr(acao_service, "obter", lambda *_a, **_k: acao)
    db.scalars.return_value.all.return_value = [vinculo(UNIDADE_A)]
    assert cliente.get(f"/api/v1/acoes/{uuid.uuid4()}/inscricoes").status_code == 403


# ---------------------------------------------------------------------
# Unidades: papel e escopo
# ---------------------------------------------------------------------

UNIDADE_JSON = {"nome": "Centro", "cidade": "Belo Horizonte", "uf": "MG"}


def test_operador_nao_cria_unidade(cliente, db):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    db.scalars.return_value.all.return_value = [vinculo(None, PapelMembro.OPERADOR)]
    resposta = cliente.post(f"/api/v1/ongs/{ONG}/unidades", json=UNIDADE_JSON)
    assert resposta.status_code == 403


def test_gestor_de_unidade_nao_cria_unidade(cliente, db):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    db.scalars.return_value.all.return_value = [vinculo(UNIDADE_A, PapelMembro.GESTOR)]
    resposta = cliente.post(f"/api/v1/ongs/{ONG}/unidades", json=UNIDADE_JSON)
    assert resposta.status_code == 403


def test_gestor_da_ong_cria_unidade(cliente, db, monkeypatch):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    db.scalars.return_value.all.return_value = [vinculo(None, PapelMembro.GESTOR)]
    criada = SimpleNamespace(
        id=uuid.uuid4(), ong_id=ONG, cep=None, logradouro=None, numero=None,
        complemento=None, bairro=None, **UNIDADE_JSON,
    )
    monkeypatch.setattr(ong_service, "criar_unidade", lambda *_: criada)
    resposta = cliente.post(f"/api/v1/ongs/{ONG}/unidades", json=UNIDADE_JSON)
    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Centro"


def test_gestor_de_unidade_edita_so_a_propria(cliente, db, monkeypatch):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    db.scalars.return_value.all.return_value = [vinculo(UNIDADE_A, PapelMembro.GESTOR)]
    monkeypatch.setattr(
        ong_service, "atualizar_unidade",
        lambda *_: SimpleNamespace(
            id=UNIDADE_A, ong_id=ONG, cep=None, logradouro=None, numero=None,
            complemento=None, bairro=None, **UNIDADE_JSON,
        ),
    )
    ok = cliente.patch(f"/api/v1/ongs/{ONG}/unidades/{UNIDADE_A}", json={"nome": "Centro"})
    negado = cliente.patch(f"/api/v1/ongs/{ONG}/unidades/{UNIDADE_B}", json={"nome": "Outra"})
    assert ok.status_code == 200
    assert negado.status_code == 403


def test_cadastro_de_ong_valida_campos(cliente):
    resposta = cliente.post("/api/v1/ongs", json={
        "nome": "ONG Teste", "email": "ong@exemplo.com", "senha": "curta",
    })
    assert resposta.status_code == 422


# ---------------------------------------------------------------------
# Perfil e refresh
# ---------------------------------------------------------------------

def test_perfil_so_para_voluntario(cliente):
    cliente.estado["usuario"] = usuario(TipoUsuario.ONG)
    assert cliente.get("/api/v1/voluntarios/eu").status_code == 403


def test_perfil_rejeita_menor_de_16(cliente):
    cliente.estado["usuario"] = usuario(TipoUsuario.VOLUNTARIO)
    ano = dt.date.today().year - 10
    resposta = cliente.put("/api/v1/voluntarios/eu", json={"data_nascimento": f"{ano}-01-01"})
    assert resposta.status_code == 422


def test_perfil_rejeita_janela_invertida(cliente):
    cliente.estado["usuario"] = usuario(TipoUsuario.VOLUNTARIO)
    resposta = cliente.put("/api/v1/voluntarios/eu", json={
        "disponibilidade": [{"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "08:00"}],
    })
    assert resposta.status_code == 422


def test_refresh_troca_tokens(cliente, db):
    conta = usuario(TipoUsuario.VOLUNTARIO)
    db.get.return_value = conta
    resposta = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": criar_refresh_token(conta.id)}
    )
    assert resposta.status_code == 200
    assert resposta.json()["access_token"]


def test_refresh_recusa_access_token(cliente, db):
    conta = usuario(TipoUsuario.VOLUNTARIO)
    db.get.return_value = conta
    token = criar_access_token(conta.id, "voluntario")
    resposta = cliente.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert resposta.status_code == 401


def test_refresh_de_conta_desativada(db):
    conta = usuario(TipoUsuario.VOLUNTARIO, ativo=False)
    db.get.return_value = conta
    from app.core.exceptions import UsuarioInativo
    with pytest.raises(UsuarioInativo):
        auth_service.renovar(db, criar_refresh_token(conta.id))


def test_rotas_do_plano_existem():
    caminhos = app.openapi()["paths"]
    for caminho, metodo in [
        ("/api/v1/ongs", "post"), ("/api/v1/ongs", "get"), ("/api/v1/ongs/{ong_id}", "get"),
        ("/api/v1/ongs/{ong_id}/unidades", "post"),
        ("/api/v1/ongs/{ong_id}/unidades/{unidade_id}", "delete"),
        ("/api/v1/voluntarios/eu", "put"), ("/api/v1/voluntarios/eu/historico", "get"),
        ("/api/v1/habilidades", "get"), ("/api/v1/acoes/{acao_id}/inscricoes", "get"),
        ("/api/v1/notificacoes", "get"), ("/api/v1/notificacoes/{notificacao_id}/lida", "post"),
        ("/api/v1/notificacoes/lidas", "post"), ("/api/v1/auth/refresh", "post"),
        ("/api/v1/estatisticas", "get"),
    ]:
        assert metodo in caminhos.get(caminho, {}), f"{metodo.upper()} {caminho}"
