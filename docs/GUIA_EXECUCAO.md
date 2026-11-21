# Guia de execução e roteiro de demonstração

## 1. Subir tudo com Docker (recomendado)

Pré-requisito: Docker Desktop (ou Docker Engine + Compose v2).

```bash
docker compose up --build
```

| Serviço | Endereço | O que é |
| --- | --- | --- |
| Interface web | http://localhost:8080 | React servido pelo nginx, que encaminha `/api` e `/ws` |
| API REST | http://localhost:8000/docs | FastAPI (Swagger) |
| Servidor VAP | `localhost:5050` (TCP) | protocolo próprio, ver `docs/VAP.md` |
| PostgreSQL | `localhost:5433` | usuário `voluntiva`, senha `voluntiva` |

Na primeira subida o banco é criado do zero: migrations `0001` a `0004`,
senha de desenvolvimento do papel `voluntiva_app` (`db/dev/9000_…`) e o
seed (`db/dev/9100_seed_dev.sql`). A API e o VAP conectam como
`voluntiva_app`, então as policies de RLS valem de verdade.

Para recriar o banco (por exemplo, para as datas do seed voltarem a ser
futuras):

```bash
docker compose down -v
docker compose up --build
```

### Contas do seed (senha `voluntiva123`)

| E-mail | Perfil |
| --- | --- |
| `voluntario@voluntiva.dev` | voluntária com habilidades (cozinha, logística) e disponível todos os dias das 6h às 18h |
| `voluntario2@voluntiva.dev` | voluntário sem perfil preenchido |
| `ong@voluntiva.dev` | proprietária do Instituto Raízes (duas unidades) |
| `operador@voluntiva.dev` | operador só da unidade Barreiro do Instituto Raízes |
| `ong2@voluntiva.dev` | proprietária da ONG Patas Unidas |
| `admin@voluntiva.dev` | administrador (acesso a todas as ONGs) |

Em `npm run dev` a tela de login mostra atalhos para as duas primeiras
contas; no build de produção eles não aparecem.

## 2. Rodar sem Docker

Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt     # Linux/macOS: .venv/bin/
cp ../.env.example ../.env                           # editar DATABASE_URL e JWT_SECRET
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
.venv/Scripts/python -m protocol                     # servidor VAP
```

Frontend (Node 22):

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev                                          # http://localhost:5173
```

O Vite encaminha `/api` e `/ws` para o backend, então não há CORS em
desenvolvimento.

Banco: aplicar `db/migrations/*.sql` em ordem (SQL Editor do Supabase ou
`psql`). Em banco local, aplicar também `db/dev/*.sql`. **Nunca** aplicar
`db/dev/` no Supabase.

## 3. Testes

```bash
cd backend
python -m pytest -m "not integracao"     # unitários, sem banco
```

Integração (exige o banco do compose no ar):

```bash
DATABASE_URL=postgresql+psycopg://voluntiva_app:voluntiva_app_dev@localhost:5433/voluntiva \
  python -m pytest -m integracao
```

A CI (`.github/workflows/ci.yml`) roda três jobs: frontend (build, lint,
typecheck), backend (unitários) e integração (Postgres 17 do zero,
migrations, seed e os testes de `tests/integracao/`).

## 4. Roteiro de demonstração (cerca de 15 minutos)

1. **Visitante.** Abra http://localhost:8080. Mostre os números da página
   inicial, a busca de ações por causa, estado e data, e a lista de ONGs.
2. **Voluntária.** Entre como `voluntario@voluntiva.dev`. Em *Ações*, marque
   "Compatíveis comigo" (RF004: o servidor cruza habilidades e
   disponibilidade). Abra "Distribuição de cestas básicas": ela já está
   inscrita. Em *Meu painel > Histórico* aparecem o plantio de mudas e as 3
   horas registradas.
3. **ONG.** Em outra janela anônima, entre como `ong@voluntiva.dev`. Crie
   uma ação publicada numa data em que a voluntária esteja disponível e
   com a habilidade "Cozinha e alimentação". A voluntária recebe a
   notificação na hora (sino e aviso na tela), pelo WebSocket.
4. **Edição e cancelamento.** Mude o horário da ação em que a voluntária
   está inscrita: ela é avisada. Tente reduzir as vagas abaixo do número de
   inscritos: o sistema recusa. Cancele a ação: os inscritos são avisados.
5. **Isolamento entre ONGs.** Entre como `operador@voluntiva.dev`: ele só vê
   e cria ações da unidade Barreiro e não pode criar unidades. Pela API
   (Swagger), um `PATCH /api/v1/acoes/{id}` de ação do Instituto Raízes com o
   token de `ong2@voluntiva.dev` devolve 403.
6. **Disputa pela última vaga (VAP).** A "Oficina de culinária (1 vaga)" tem
   uma vaga. Obtenha os tokens de dois voluntários em
   `POST /api/v1/auth/login` e, em dois terminais, rode ao mesmo tempo:

   ```bash
   cd backend
   python -m protocol.client --token <TOKEN_1> LIST_ACTIONS
   python -m protocol.client --token <TOKEN_1> REGISTER_ACTION '{"action_id": <codigo>}'
   python -m protocol.client --token <TOKEN_2> REGISTER_ACTION '{"action_id": <codigo>}'
   ```

   Um recebe `201 CREATED` e o outro `409 CONFLICT` ("Ação social lotada"):
   quem decide é o trigger com `SELECT … FOR UPDATE` no PostgreSQL, não a
   memória do servidor. O mesmo vale misturando REST e VAP.

   Repita o segundo pedido com `{"action_id": <codigo>, "waitlist": true}`:
   ele entra na lista de espera (`WAITLISTED`). Quando o primeiro cancelar
   (`CANCEL_REGISTRATION`), o segundo é confirmado na hora e recebe a
   notificação "Sua vaga foi confirmada". Na interface web, o botão
   "Entrar na lista de espera" aparece quando a ação está lotada.
7. **Presença.** No painel da ONG, aba *Presença*, faça check-in e check-out
   de um inscrito numa ação do dia: as horas são calculadas pelo banco e
   aparecem no histórico do voluntário. O mesmo pelo VAP:
   `CHECK_IN` / `CHECK_OUT` com `{"action_id": …, "volunteer_email": "…"}`.

## 5. Limitações conhecidas

- **Tokens em `localStorage`.** Aceitável para o protótipo; em produção, o
  correto é cookie `httpOnly` + `SameSite`, definido pelo backend.
- **TLS no VAP** é suportado (`VAP_USE_TLS`), mas o cliente de
  desenvolvimento não verifica o certificado.
- **Tempo real só pela API.** Notificações geradas por comandos VAP ficam
  gravadas, mas só chegam à interface web na próxima carga (o WebSocket
  vive no processo da API). Com várias réplicas da API, o gerenciador de
  conexões em memória precisaria de Redis ou `LISTEN/NOTIFY`.
- **Refresh token sem revogação.** Um refresh token vale até expirar;
  desativar a conta corta o acesso.
