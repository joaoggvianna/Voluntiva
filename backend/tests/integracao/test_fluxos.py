"""Fluxos ponta a ponta contra PostgreSQL real (ver conftest.py)."""
import datetime as dt
import threading
import uuid

from sqlalchemy import text

from app.core.exceptions import ConflitoDeEstado
from app.db.session import SessionLocal
from app.services import inscricao_service

UTC = dt.timezone.utc


def _iso(instante: dt.datetime) -> str:
    return instante.astimezone(UTC).isoformat()


def _criar_acao(cliente, cabecalhos, ong_id, unidade_id, *, vagas=5, dias=3, horas=(9, 12),
                status="publicada", habilidades=None, inicio=None, fim=None):
    if inicio is None:
        base = (dt.datetime.now(UTC) + dt.timedelta(days=dias)).replace(
            minute=0, second=0, microsecond=0
        )
        inicio = base.replace(hour=horas[0] + 3)  # 09h em São Paulo = 12h UTC
        fim = base.replace(hour=horas[1] + 3)
    resposta = cliente.post("/api/v1/acoes", headers=cabecalhos, json={
        "ong_id": ong_id, "unidade_id": unidade_id, "titulo": "Ação de integração",
        "descricao": "Descrição longa o bastante para a ação de teste.",
        "inicio": _iso(inicio), "fim": _iso(fim), "vagas": vagas, "status": status,
        "habilidades": habilidades or [],
    })
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _usuario_id(cliente, cabecalhos) -> uuid.UUID:
    return uuid.UUID(cliente.get("/api/v1/auth/eu", headers=cabecalhos).json()["id"])


# ---------------------------------------------------------------------
# Banco e papel da aplicação
# ---------------------------------------------------------------------

def test_backend_conecta_com_papel_da_aplicacao_e_rls_forcado(banco_disponivel):
    with SessionLocal() as db:
        papel = db.execute(text("SELECT current_user")).scalar()
        forcadas = db.execute(text("""
            SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relforcerowsecurity
        """)).scalar()
        policies = db.execute(text(
            "SELECT count(*) FROM pg_policies WHERE schemaname = 'public' AND 'voluntiva_app' = ANY(roles)"
        )).scalar()
        habilidades = db.execute(text("SELECT count(*) FROM public.habilidade")).scalar()
    # Em CI e no compose o backend usa voluntiva_app; se alguém rodar como
    # superusuário, o RLS não é exercitado e o teste avisa.
    assert papel == "voluntiva_app", f"backend conectado como {papel}"
    assert forcadas == 13
    assert policies == 13
    assert habilidades > 0  # a policy libera leitura para o papel


# ---------------------------------------------------------------------
# Lotação sob concorrência
# ---------------------------------------------------------------------

def test_disputa_pela_ultima_vaga(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, vagas=1)
    candidatos = [_usuario_id(cliente, novo_voluntario()[1]) for _ in range(4)]

    resultados, barreira = [], threading.Barrier(len(candidatos))

    def tentar(usuario_id):
        with SessionLocal() as db:
            barreira.wait()
            try:
                inscricao_service.inscrever(db, usuario_id, uuid.UUID(acao["id"]))
                resultados.append("ok")
            except ConflitoDeEstado as exc:
                resultados.append(exc.mensagem)

    threads = [threading.Thread(target=tentar, args=(u,)) for u in candidatos]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert resultados.count("ok") == 1, resultados
    assert all(r == "Ação social lotada" for r in resultados if r != "ok"), resultados
    detalhe = cliente.get(f"/api/v1/acoes/{acao['id']}").json()
    assert detalhe["vagas_ocupadas"] == 1 and detalhe["vagas_disponiveis"] == 0


# ---------------------------------------------------------------------
# Autorização entre ONGs
# ---------------------------------------------------------------------

def test_ong_nao_altera_acao_de_outra_ong(cliente, nova_ong):
    ong_a, unidade_a, cab_a = nova_ong()
    _, unidade_b, cab_b = nova_ong()
    acao = _criar_acao(cliente, cab_a, ong_a, unidade_a)

    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_b,
                         json={"titulo": "Invadido"}).status_code == 403
    # Nem criar ação na ONG A, nem usar unidade da ONG B numa ação da A.
    assert cliente.post("/api/v1/acoes", headers=cab_b, json={
        "ong_id": ong_a, "titulo": "Xyz", "inicio": acao["inicio"], "fim": acao["fim"], "vagas": 1,
    }).status_code == 403
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_a,
                         json={"unidade_id": unidade_b}).status_code in (403, 422)
    assert cliente.get(f"/api/v1/acoes/{acao['id']}/inscricoes", headers=cab_b).status_code == 403


def test_rascunho_so_aparece_para_a_ong(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, status="rascunho")
    _, cab_vol = novo_voluntario()

    assert cliente.get(f"/api/v1/acoes/{acao['id']}").status_code == 404
    assert cliente.get(f"/api/v1/acoes/{acao['id']}", headers=cab_vol).status_code == 404
    assert cliente.get(f"/api/v1/acoes/{acao['id']}", headers=cab_ong).status_code == 200
    lista = cliente.get("/api/v1/acoes", headers=cab_ong,
                        params={"ong_id": ong_id, "todos_status": "true"})
    assert lista.status_code == 200 and lista.headers["X-Total-Count"] == "1"


# ---------------------------------------------------------------------
# Edição, cancelamento e notificações
# ---------------------------------------------------------------------

def test_cancelar_acao_notifica_inscritos(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, vagas=3)
    _, cab_vol = novo_voluntario()
    assert cliente.post("/api/v1/inscricoes", headers=cab_vol,
                        json={"acao_id": acao["id"]}).status_code == 201

    # Gestor da ONG foi avisado da inscrição.
    avisos_ong = cliente.get("/api/v1/notificacoes", headers=cab_ong).json()
    assert any(n["tipo"] == "inscricao_confirmada" and n["acao_id"] == acao["id"] for n in avisos_ong)

    # Não dá para reduzir vagas abaixo dos confirmados (1).
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                         json={"vagas": 0}).status_code == 422  # ge=1 no schema
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                         json={"vagas": 1}).status_code == 200

    resposta = cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                             json={"status": "cancelada"})
    assert resposta.status_code == 200
    avisos = cliente.get("/api/v1/notificacoes", headers=cab_vol).json()
    assert any(n["tipo"] == "acao_cancelada" and n["acao_id"] == acao["id"] for n in avisos)
    assert cliente.get("/api/v1/notificacoes/nao-lidas", headers=cab_vol).json()["nao_lidas"] >= 1
    assert cliente.post("/api/v1/notificacoes/lidas", headers=cab_vol).json()["marcadas"] >= 1

    # Estado final: ação cancelada não volta a ser publicada.
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                         json={"status": "publicada"}).status_code == 409


def test_reduzir_vagas_abaixo_dos_confirmados(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, vagas=3)
    for _ in range(2):
        _, cab = novo_voluntario()
        assert cliente.post("/api/v1/inscricoes", headers=cab,
                            json={"acao_id": acao["id"]}).status_code == 201
    resposta = cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong, json={"vagas": 1})
    assert resposta.status_code == 409


# ---------------------------------------------------------------------
# RF004, perfil, presença e histórico
# ---------------------------------------------------------------------

def test_acoes_compativeis_com_o_perfil(cliente, nova_ong, novo_voluntario):
    habilidades = cliente.get("/api/v1/habilidades").json()
    cozinha = next(h["id"] for h in habilidades if h["nome"] == "Cozinha e alimentação")
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, habilidades=[cozinha], dias=6)
    dia = (dt.datetime.fromisoformat(acao["inicio"]).astimezone(
        dt.timezone(dt.timedelta(hours=-3))).isoweekday() % 7)

    _, cab_ok = novo_voluntario()
    perfil = cliente.put("/api/v1/voluntarios/eu", headers=cab_ok, json={
        "habilidades": [{"habilidade_id": cozinha}],
        "disponibilidade": [{"dia_semana": dia, "hora_inicio": "06:00", "hora_fim": "18:00"}],
    })
    assert perfil.status_code == 200, perfil.text
    assert perfil.json()["habilidades"][0]["nome"] == "Cozinha e alimentação"

    _, cab_sem = novo_voluntario()  # sem disponibilidade
    ids_ok = {a["acao_id"] for a in cliente.get("/api/v1/acoes/compativeis", headers=cab_ok).json()}
    ids_sem = {a["acao_id"] for a in cliente.get("/api/v1/acoes/compativeis", headers=cab_sem).json()}
    assert acao["id"] in ids_ok
    assert acao["id"] not in ids_sem


def test_presenca_e_historico(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    agora = dt.datetime.now(UTC)
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id,
                       inicio=agora + dt.timedelta(minutes=5),
                       fim=agora + dt.timedelta(minutes=65))
    email, cab_vol = novo_voluntario()
    inscricao = cliente.post("/api/v1/inscricoes", headers=cab_vol, json={"acao_id": acao["id"]})
    assert inscricao.status_code == 201
    inscricao_id = inscricao.json()["id"]

    # Voluntário não registra a própria presença.
    assert cliente.post(f"/api/v1/inscricoes/{inscricao_id}/check-in",
                        headers=cab_vol).status_code == 403
    assert cliente.post(f"/api/v1/inscricoes/{inscricao_id}/check-in",
                        headers=cab_ong).status_code == 201
    saida = cliente.post(f"/api/v1/inscricoes/{inscricao_id}/check-out", headers=cab_ong)
    assert saida.status_code == 200 and saida.json()["horas_computadas"] is not None

    inscritos = cliente.get(f"/api/v1/acoes/{acao['id']}/inscricoes", headers=cab_ong).json()
    assert inscritos[0]["email"] == email and inscritos[0]["check_out"] is not None

    minhas = cliente.get("/api/v1/inscricoes/minhas", headers=cab_vol).json()
    assert minhas[0]["acao"]["id"] == acao["id"] and minhas[0]["check_in"] is not None

    # Concluída, a ação entra no histórico com as horas.
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                         json={"status": "concluida"}).status_code == 200
    historico = cliente.get("/api/v1/voluntarios/eu/historico", headers=cab_vol).json()
    assert historico["total_acoes"] == 1 and historico["presencas"] == 1


def test_consultas_publicas(cliente, nova_ong):
    ong_id, unidade_id, cab_ong = nova_ong(causa="saude")
    _criar_acao(cliente, cab_ong, ong_id, unidade_id)
    estatisticas = cliente.get("/api/v1/estatisticas").json()
    assert estatisticas["ongs"] >= 1 and estatisticas["acoes_abertas"] >= 1

    ongs = cliente.get("/api/v1/ongs", params={"causa": "saude", "uf": "MG"}).json()
    assert any(o["id"] == ong_id and o["acoes_abertas"] >= 1 for o in ongs)

    filtradas = cliente.get("/api/v1/acoes", params={
        "ong_id": ong_id, "busca": "integração", "uf": "MG", "com_vagas": "true",
        "futuras": "true", "de": dt.date.today().isoformat(),
    })
    assert filtradas.status_code == 200 and int(filtradas.headers["X-Total-Count"]) == 1


def test_refresh_token(cliente, novo_voluntario):
    email, _ = novo_voluntario()
    login = cliente.post("/api/v1/auth/login", json={"email": email, "senha": "senha-de-teste-123"}).json()
    novo = cliente.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert novo.status_code == 200 and novo.json()["usuario"]["email"] == email


# ---------------------------------------------------------------------
# Lista de espera
# ---------------------------------------------------------------------

def test_lista_de_espera_promove_quando_abre_vaga(cliente, nova_ong, novo_voluntario):
    ong_id, unidade_id, cab_ong = nova_ong()
    acao = _criar_acao(cliente, cab_ong, ong_id, unidade_id, vagas=1)
    _, cab_primeira = novo_voluntario()
    _, cab_segunda = novo_voluntario()
    _, cab_terceira = novo_voluntario()

    assert cliente.post("/api/v1/inscricoes", headers=cab_primeira,
                        json={"acao_id": acao["id"]}).json()["status"] == "confirmada"
    # Sem pedir a fila, ação lotada continua recusando.
    assert cliente.post("/api/v1/inscricoes", headers=cab_segunda,
                        json={"acao_id": acao["id"]}).status_code == 409
    for cab in (cab_segunda, cab_terceira):
        resposta = cliente.post("/api/v1/inscricoes", headers=cab,
                                json={"acao_id": acao["id"], "lista_espera": True})
        assert resposta.status_code == 201 and resposta.json()["status"] == "lista_espera"
    assert cliente.get(f"/api/v1/acoes/{acao['id']}").json()["em_lista_espera"] == 2

    # A confirmada desiste: a segunda (primeira da fila) é promovida e avisada.
    assert cliente.request("DELETE", f"/api/v1/inscricoes/{acao['id']}",
                           headers=cab_primeira).status_code == 200
    minhas = cliente.get("/api/v1/inscricoes/minhas", headers=cab_segunda).json()
    assert minhas[0]["status"] == "confirmada"
    avisos = cliente.get("/api/v1/notificacoes", headers=cab_segunda).json()
    assert any(n["titulo"] == "Sua vaga foi confirmada" for n in avisos)
    terceira = cliente.get("/api/v1/inscricoes/minhas", headers=cab_terceira).json()
    assert terceira[0]["status"] == "lista_espera"

    # A ONG aumenta as vagas: a terceira também entra.
    assert cliente.patch(f"/api/v1/acoes/{acao['id']}", headers=cab_ong,
                         json={"vagas": 2}).status_code == 200
    terceira = cliente.get("/api/v1/inscricoes/minhas", headers=cab_terceira).json()
    assert terceira[0]["status"] == "confirmada"
    detalhe = cliente.get(f"/api/v1/acoes/{acao['id']}").json()
    assert detalhe["vagas_ocupadas"] == 2 and detalhe["em_lista_espera"] == 0
