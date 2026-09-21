# Voluntiva

**Voluntiva** é um sistema de gestão de voluntários voltado a organizações não governamentais (ONGs), desenvolvido como projeto acadêmico integrando as disciplinas de **Laboratório de Projeto de Software**, **Projeto de Protocolo de Redes** e **Laboratório de Banco de Dados**.

## Objetivo

O projeto tem como objetivo centralizar e facilitar a gestão de voluntários, ações sociais e inscrições em eventos promovidos por ONGs. A plataforma deverá permitir que organizações cadastrem oportunidades de voluntariado e que voluntários encontrem ações compatíveis com seu perfil, habilidades e disponibilidade.

## Funcionalidades previstas

- Cadastro e autenticação de voluntários e ONGs;
- Cadastro de unidades e ações sociais;
- Consulta de oportunidades de voluntariado;
- Inscrição e cancelamento de participação em ações;
- Registro de habilidades e disponibilidade dos voluntários;
- Controle de presença e histórico de participação;
- Notificações sobre criação, atualização ou cancelamento de ações;
- Gestão das informações por meio de um banco de dados relacional.

## Relação com as disciplinas

### Laboratório de Projeto de Software

Responsável pela definição de requisitos, casos de uso, arquitetura da aplicação, regras de negócio, interface e organização dos módulos do sistema.

### Projeto de Protocolo de Redes

A aplicação utilizará uma arquitetura cliente-servidor. A comunicação entre clientes e servidor será feita por meio de um protocolo de aplicação próprio sobre TCP, com mensagens para operações como autenticação, consulta de eventos, inscrições, atualizações e notificações.

Exemplos de comandos previstos:

```text
LOGIN
LIST_EVENTS
JOIN_EVENT
LEAVE_EVENT
CREATE_EVENT
UPDATE_EVENT
CHECK_IN
CHECK_OUT
PING
PONG
```

### Laboratório de Banco de Dados

O banco de dados armazenará informações relacionadas a voluntários, ONGs, unidades, ações sociais, habilidades, inscrições, presença e histórico de participação.

Entidades iniciais previstas:

- Voluntário;
- ONG;
- Unidade;
- Evento/Ação Social;
- Habilidade;
- Inscrição;
- Presença;
- Usuário.

## Arquitetura inicial

```text
Cliente Voluntário ─┐
                    │
Cliente ONG ─────────┼── TCP / Protocolo Voluntiva ── Servidor ── Banco de Dados
                    │
Cliente Unidade ─────┘
```

## Identidade visual do frontend

A interface web seguirá uma identidade visual acolhedora, moderna e ligada à ideia de comunidade e impacto social.

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
├── backend/            # Python
│   ├── app/            # API REST + WebSocket (FastAPI)
│   │   ├── api/v1/     # rotas HTTP
│   │   ├── services/   # regra de negócio (fonte única, usada pelos dois transportes)
│   │   ├── models/     # SQLAlchemy — mapeia o schema, não o gera
│   │   └── core/       # config, segurança (JWT/Argon2), exceções de domínio
│   ├── protocol/       # servidor do protocolo VAP sobre TCP puro
│   └── tests/          # pytest (app/ e protocol/)
├── db/migrations/      # fonte da verdade do schema, em SQL numerado
├── docs/               # VAP.md e SECURITY.md — especificação do protocolo
└── frontend/           # React + Vite + Tailwind (ver frontend/README.md)
```

Os dois transportes — HTTP e VAP — chamam **as mesmas funções** de
`backend/app/services/`. Regra de negócio nunca é reimplementada dentro
de `protocol/`; cada transporte só traduz a exceção de domínio para o seu
próprio formato de erro.

## Como executar

### Backend

```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt   # Windows
cp ../.env.example ../.env    # editar DATABASE_URL e JWT_SECRET

.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000   # API REST
.venv/Scripts/python -m protocol                                    # servidor VAP (porta 5050)
.venv/Scripts/python -m pytest                                      # testes (não exigem banco)
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

### Banco

As migrations em `db/migrations/` são aplicadas **em ordem**, no SQL
Editor do Supabase ou num Postgres local. O schema não é gerado pelo ORM:
nunca rode `Base.metadata.create_all()`.

## Protocolo VAP

O protocolo próprio da aplicação, sobre TCP, está especificado em
[docs/VAP.md](docs/VAP.md); as proteções implementadas e as limitações
conhecidas, em [docs/SECURITY.md](docs/SECURITY.md).

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
ambiente virtual, execute `python -m protocol.client`.

## Estado do projeto

**Funcionando e testado ponta a ponta** (REST + VAP contra Postgres
real): registro, login, listagem de ações, inscrição, cancelamento,
reinscrição, disputa da última vaga, check-in/check-out com cálculo de
horas.

**Pendente** (marcado com `TODO(equipe)` no código):

- `CREATE_EVENT` / `UPDATE_EVENT` e `LIST_NOTIFICATIONS` no VAP;
- decisão sobre `CHECK_IN`/`CHECK_OUT` entrarem ou não na spec do VAP;
- filtro por habilidade e disponibilidade do voluntário (RF004);
- ligar as telas do frontend à API real (hoje usam mock em `localStorage`);
- `docker-compose.yml` e guia de setup;
- TLS no servidor VAP e cookie `httpOnly` no lugar do `localStorage` para o JWT.
