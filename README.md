# Voluntiva

**Voluntiva** é um sistema de gestão de voluntários voltado a organizações não governamentais (ONGs), desenvolvido como projeto acadêmico integrando as disciplinas de **Laboratório de Projeto de Software**, **Projeto de Protocolo de Redes** e **Laboratório de Banco de Dados**.

## No ar

| | Endereço |
| --- | --- |
| Site | https://voluntiva-web-nb88.onrender.com |
| API | https://voluntiva-api-nb88.onrender.com (saúde em [`/health`](https://voluntiva-api-nb88.onrender.com/health)) |

Tudo roda em planos gratuitos: interface e API no Render, banco no
Supabase. O servidor do protocolo VAP (TCP puro) não é publicado, porque
nenhum plano gratuito aceita TCP cru; ele roda localmente, ligado ao mesmo
banco, só para a demonstração. Passo a passo em
[docs/DEPLOY.md](docs/DEPLOY.md).

No plano gratuito a API dorme após 15 minutos sem acesso; a primeira
requisição depois disso leva cerca de 1 minuto.

## Objetivo

O projeto centraliza e facilita a gestão de voluntários, ações sociais e inscrições em eventos promovidos por ONGs. Organizações cadastram oportunidades de voluntariado e voluntários encontram ações compatíveis com seu perfil, habilidades e disponibilidade.

## Funcionalidades

- Cadastro e autenticação de voluntários e ONGs;
- ONGs com unidades e membros com papéis (proprietário, gestor, operador);
- Cadastro, publicação, edição e cancelamento de ações sociais;
- Consulta de oportunidades com filtros e paginação;
- Inscrição e cancelamento, com lista de espera e promoção automática;
- Habilidades e disponibilidade do voluntário, e filtro de ações compatíveis;
- Check-in e check-out, com horas calculadas pelo banco, e histórico de participação;
- Notificações sobre criação, alteração e cancelamento de ações, em tempo real;
- Banco de dados relacional com RLS e regras de integridade no próprio banco.

## Relação com as disciplinas

### Laboratório de Projeto de Software

Responsável pela definição de requisitos, casos de uso, arquitetura da aplicação, regras de negócio, interface e organização dos módulos do sistema.

### Projeto de Protocolo de Redes

Além da API HTTP usada pelo site, a aplicação tem um protocolo de aplicação próprio sobre TCP, o **VAP**, com mensagens para autenticação, consulta de ações, inscrições, gestão de ações, presença e notificações.

Comandos implementados (especificação completa em [docs/VAP.md](docs/VAP.md)):

```text
PING                 AUTH
LIST_ACTIONS         REGISTER_ACTION      CANCEL_REGISTRATION
CREATE_ACTION        UPDATE_ACTION
CHECK_IN             CHECK_OUT
LIST_NOTIFICATIONS
```

### Laboratório de Banco de Dados

O banco PostgreSQL (Supabase) guarda voluntários, ONGs, unidades e membros, ações sociais, habilidades, disponibilidade, inscrições, presença e notificações. O schema vive em migrations SQL numeradas, com enums, triggers, views e RLS que o ORM não gera.

Entidades principais:

- Usuário, Voluntário e ONG;
- Unidade e membro da ONG;
- Ação social e habilidade;
- Inscrição e presença;
- Notificação.

## Arquitetura

```text
                ┌── HTTPS ── API REST (FastAPI) ──┐
Navegador ──────┤                                 │
(React)         └── WSS ──── notificações ────────┤
                                                  ├── services/ ──── PostgreSQL
Cliente TCP ─────── TCP ──── servidor VAP ────────┘  (mesmas regras)  (Supabase)
```

Os dois transportes, HTTP e VAP, chamam **as mesmas funções** de
`backend/app/services/`. Regra de negócio nunca é reimplementada dentro
de `protocol/`; cada transporte só traduz a exceção de domínio para o seu
próprio formato de erro.

## Identidade visual do frontend

A interface web segue uma identidade visual acolhedora, moderna e ligada à ideia de comunidade e impacto social.

### Paleta principal

| Uso | Cor | Hex |
| --- | --- | --- |
| Primária | Azul petróleo | `#1F5F63` |
| Secundária | Azul claro suave | `#DDEFF0` |
| Destaque | Coral | `#F27A5A` |
| Fundo | Off-white | `#F8FAF9` |
| Texto | Grafite | `#263238` |
| Bordas | Cinza claro | `#D9E2E1` |

### Cores de estado

| Estado | Hex |
| --- | --- |
| Sucesso | `#3F7D58` |
| Aviso | `#D99A35` |
| Erro | `#C94C4C` |

### Diretrizes de uso

- Aproximadamente **70% de tons neutros**, **20% de azul petróleo** e **10% de coral**;
- Azul petróleo para identidade, navegação, ícones e ações secundárias;
- Coral reservado principalmente para CTAs e ações importantes;
- Fundo majoritariamente off-white ou branco para manter leveza e legibilidade;
- Cards com bordas discretas e contraste moderado, evitando excesso de cores e gradientes;
- A interface deve transmitir confiança, proximidade e organização sem assumir uma estética corporativa excessiva.

Exemplo de variáveis CSS:

```css
:root {
  --primary: #1F5F63;
  --primary-light: #DDEFF0;
  --accent: #F27A5A;
  --background: #F8FAF9;
  --surface: #FFFFFF;
  --text: #263238;
  --text-muted: #6B7777;
  --border: #D9E2E1;
  --success: #3F7D58;
  --warning: #D99A35;
  --danger: #C94C4C;
}
```

## Equipe

- Carlos Gabriel Gouveia
- João Gabriel Guedes Vianna
- João Guilherme Costa Couto
- João Victor Pereira Bicalho
- Mateus Munhoz Guimarães

## Estrutura do repositório

```text
.
├── backend/            # Python 3.12
│   ├── app/            # API REST + WebSocket (FastAPI)
│   │   ├── api/v1/     # rotas HTTP e o WebSocket de notificações
│   │   ├── services/   # regra de negócio (fonte única, usada pelos dois transportes)
│   │   ├── models/     # SQLAlchemy: mapeia o schema, não o gera
│   │   ├── realtime/   # conexões WebSocket ativas e entrega de notificações
│   │   └── core/       # config, segurança (JWT/Argon2), limites, exceções de domínio
│   ├── protocol/       # servidor do protocolo VAP sobre TCP puro
│   └── tests/          # pytest: unitários, VAP e integração (tests/integracao/)
├── db/migrations/      # fonte da verdade do schema, em SQL numerado
├── db/dev/             # SÓ desenvolvimento: senha do papel da app e seed (públicas)
├── docs/               # DEPLOY, GUIA_EXECUCAO, VAP, SECURITY, VALIDACAO_AUTORIZACAO
├── frontend/           # React + Vite + Tailwind (ver frontend/README.md)
├── docker-compose.yml  # banco, API, VAP e web para rodar local
├── render.yaml         # Blueprint do deploy gratuito no Render
└── .github/workflows/  # CI: frontend, backend e integração com PostgreSQL
```

## Como executar

O caminho mais curto é o Docker Compose, que sobe banco (com migrations e
contas de teste), API, servidor VAP e interface web:

```bash
docker compose up --build    # web em http://localhost:8080
```

O passo a passo completo, as contas do seed e o roteiro de demonstração
estão em [docs/GUIA_EXECUCAO.md](docs/GUIA_EXECUCAO.md).

### Backend

```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt   # Windows
cp ../.env.example ../.env    # editar DATABASE_URL e JWT_SECRET

.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000   # API REST
.venv/Scripts/python -m protocol                                    # servidor VAP (porta 5050)
```

Em Linux/macOS troque `.venv/Scripts/` por `.venv/bin/`.

`DATABASE_URL` deve usar a porta **5432** do Supabase (Session pooler) e
não a 6543: o pooler transacional não mantém sessão entre statements, o
que quebra o `SELECT ... FOR UPDATE` do controle de lotação de vagas.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev    # http://localhost:5173
```

No Windows, se o PowerShell bloquear o `npm` pela política de scripts, use
`npm.cmd` (por exemplo, `npm.cmd run dev`).

### Banco

As migrations em `db/migrations/` são aplicadas **em ordem**, no SQL
Editor do Supabase ou num Postgres local. O schema não é gerado pelo ORM:
nunca rode `Base.metadata.create_all()`.

A `0003` cria o papel `voluntiva_app` (só DML) e as policies de RLS que
liberam as tabelas para ele. Depois de aplicá-la, defina a senha uma vez
e aponte o `DATABASE_URL` do backend para esse usuário:

```sql
alter role voluntiva_app with login password '<gerar-senha-forte>';
```

No Supabase, pelo pooler, o usuário fica `voluntiva_app.<project_ref>`.

> **Nunca aplique `db/dev/` no Supabase.** A senha do papel e a das
> contas do seed (`voluntiva123`) estão públicas no repositório; esses
> arquivos servem só ao Docker Compose e à CI.

### Testes

```bash
cd backend
.venv/Scripts/python -m pytest -m "not integracao"   # unitários e VAP, sem banco
.venv/Scripts/python -m pytest -m integracao         # exige PostgreSQL com as migrations

cd frontend
npm run build && npm run lint && npm run typecheck
```

A CI (`.github/workflows/ci.yml`) roda tudo a cada push: build, lint e
typecheck do frontend; ruff e testes unitários do backend; e a suíte de
integração contra um PostgreSQL novo, com todas as migrations aplicadas e
o backend conectado como `voluntiva_app` (RLS ligado).

## Protocolo VAP

O protocolo próprio da aplicação, sobre TCP, está especificado em
[docs/VAP.md](docs/VAP.md).

A implementação fica em `backend/protocol/`. Há dois modos de execução:

| Comando | Autenticação e serviços | Uso |
| --- | --- | --- |
| `python -m protocol.server` | mocks (`auth.py`, `services.py`) | testes do protocolo isolado |
| `python -m protocol` | adapters reais (`auth_db.py`, `services_db.py`) | contra o Postgres |

Não existe login por senha no VAP: o cliente autentica primeiro pela API
REST (`POST /api/v1/auth/login`), recebe o JWT e o envia no comando
`AUTH`. O servidor decodifica o token **e consulta o banco** para
confirmar que a conta continua ativa.

Para experimentar, suba o servidor e, em outro terminal com o mesmo
ambiente virtual, execute `python -m protocol.client` (demonstração com
os mocks) ou `python -m protocol.client --token <JWT> LIST_ACTIONS`
(contra o servidor real). Para a demo usar o banco de produção, o `.env`
local precisa da mesma `DATABASE_URL` e do mesmo `JWT_SECRET` do Render
(seção 7 de [docs/DEPLOY.md](docs/DEPLOY.md)).

## Segurança

O que está protegido e o que falta está em
[docs/SECURITY.md](docs/SECURITY.md). Em resumo: senhas com Argon2id, JWT
com escopo separado para access e refresh, limite de tentativas de login,
autorização por papel na ONG compartilhada entre API e VAP, RLS no banco
com um papel só de DML, consultas parametrizadas, CORS restrito ao site e
cabeçalhos de segurança (incluindo CSP) no site publicado.

## Estado do projeto

**Implementado:**

- API REST: cadastro e login (com refresh token) de voluntários e ONGs;
  ONGs, unidades e vínculos com papéis (proprietário, gestor, operador);
  ações com filtros, paginação (`X-Total-Count`), rascunho visível só para
  a ONG e regras de edição (transições de status, mínimo de vagas);
  inscrição, cancelamento, lista de espera com promoção automática e
  disputa da última vaga no banco; check-in e check-out com horas
  calculadas pelo banco; perfil do voluntário (habilidades e
  disponibilidade), histórico e filtro de compatibilidade (RF004);
  notificações gravadas na mesma transação da mudança e entregues em tempo
  real pelo WebSocket; estatísticas da página inicial.
- Interface web completa ligada à API.
- Protocolo VAP: os dez comandos listados acima, sobre os mesmos services
  da API.
- Banco: papel `voluntiva_app` com RLS (migration 0003) e causa social de
  ONGs e ações (migration 0004).
- Entrega: deploy gratuito no Render + Supabase, Docker Compose para rodar
  local, seed de desenvolvimento e CI com suíte de integração contra
  PostgreSQL.

**Limitações conhecidas** (detalhes em
[docs/SECURITY.md](docs/SECURITY.md) e
[docs/GUIA_EXECUCAO.md](docs/GUIA_EXECUCAO.md#5-limitações-conhecidas)):
tokens em `localStorage` em vez de cookie `httpOnly`; refresh token sem
revogação; cliente VAP de desenvolvimento não verifica o certificado TLS;
VAP só local; notificações geradas pelo VAP só aparecem no site na próxima
carga da página.
