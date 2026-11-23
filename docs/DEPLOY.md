# Deploy gratuito no Render

Guia para colocar o Voluntiva no ar de graça até a apresentação, com o
banco no Supabase (plano gratuito) e a API e a interface no Render
(plano gratuito). Nada aqui gera cobrança.

## Visão geral

```
navegador ──https──> voluntiva-web  (Render Static Site: React/Vite)
    │
    ├──https──> voluntiva-api  (Render Web Service free: FastAPI)
    └──wss────> voluntiva-api  /ws/notificacoes (tempo real)
                      │
                      └──Postgres (Session pooler)──> Supabase (free)

notebook ──TCP 5050──> servidor VAP local ──> mesmo Supabase
```

| Parte | Onde roda | Custo |
| --- | --- | --- |
| Interface web | Render Static Site | grátis |
| API REST + WebSocket | Render Web Service, plano Free | grátis (750 h/mês, dorme após 15 min sem acesso) |
| Banco | Supabase, plano Free | grátis (pausa após 7 dias sem acesso) |
| Servidor VAP (TCP) | **só no notebook**, durante a demo | — |

O VAP não vai para a nuvem porque nenhum plano gratuito aceita TCP cru
(o Render free só expõe HTTP/HTTPS e WebSocket). Como o VAP local usa o
mesmo banco do Supabase, o que for feito por ele aparece no site.

Tudo o que o Render precisa já está no repositório:

- `render.yaml` (Blueprint) cria os dois serviços de uma vez.
- `GET/HEAD /health` responde ao health check do Render e ao UptimeRobot.
- O frontend lê a URL da API de `VITE_API_URL` e deriva o WebSocket dela
  (`https://...` vira `wss://...`), então só uma variável é necessária.
- A API lê CORS, banco e segredo JWT de variáveis de ambiente.

---

## 1. Preparar o Supabase

Faça uma vez, no painel do projeto em https://supabase.com/dashboard.

### 1.1 Conferir as migrations

Em **SQL Editor**, confira se o schema já existe (por exemplo, se a tabela
`usuario` aparece em **Table Editor**). Se não existir, rode em ordem o
conteúdo de:

1. `db/migrations/0001_voluntiva_schema.sql`
2. `db/migrations/0002_codigo_publico_acao.sql`
3. `db/migrations/0003_rls_papel_app.sql`
4. `db/migrations/0004_causa.sql`

**Não rode nada de `db/dev/`** no Supabase: o seed e a senha de
desenvolvimento são públicos no repositório.

### 1.2 Senha do papel da aplicação

A API conecta como `voluntiva_app` (não como `postgres`), para as
policies de RLS valerem. Se essa senha ainda não foi definida, gere uma
senha forte **só com letras e números** (evita ter que fazer URL-encode)
e rode no SQL Editor:

```sql
alter role voluntiva_app with login password 'COLE_A_SENHA_AQUI';
```

Guarde a senha num gerenciador de senhas. Ela não vai para o repositório.

### 1.3 Montar a `DATABASE_URL`

No topo do painel, clique em **Connect** e escolha **Session pooler**
(porta **5432**). Não use a conexão direta (`db.<ref>.supabase.co`): ela
é só IPv6 e o Render não alcança IPv6. Não use o Transaction pooler
(porta 6543): ele quebra o `SELECT ... FOR UPDATE` do controle de vagas.

A string do Supabase vem assim:

```
postgresql://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
```

Troque três coisas:

1. `postgresql://` por `postgresql+psycopg://` (driver usado pela API);
2. o usuário `postgres.<ref>` por `voluntiva_app.<ref>` (mantenha o `<ref>`);
3. `[YOUR-PASSWORD]` pela senha do passo 1.2.

Resultado:

```
postgresql+psycopg://voluntiva_app.abcdefghijklmnop:SENHA@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
```

---

## 2. Subir o código para o GitHub

O Render lê o código direto do GitHub. Faça commit e push destas
alterações (incluindo o `render.yaml` na raiz) para a branch que será
publicada, normalmente a `main`.

---

## 3. Criar os serviços no Render

1. Crie uma conta em https://render.com entrando com o GitHub. O plano
   Free não cobra nada; se o Render pedir para autorizar o acesso aos
   repositórios, libere o repositório do Voluntiva.
2. No painel, clique em **New > Blueprint**.
3. Escolha o repositório do Voluntiva e a branch (`main`). O Render acha
   o `render.yaml` e mostra os dois serviços: `voluntiva-api` e
   `voluntiva-web`. Confirme que os dois estão como **Free**.
4. Dê um nome ao Blueprint (ex.: `voluntiva`) e preencha as variáveis
   pedidas:

   | Serviço | Variável | Valor |
   | --- | --- | --- |
   | voluntiva-api | `DATABASE_URL` | a string montada no passo 1.3 |
   | voluntiva-api | `CORS_ORIGINS` | `https://voluntiva-web.onrender.com` |
   | voluntiva-web | `VITE_API_URL` | `https://voluntiva-api.onrender.com` |

   As URLs acima são um palpite: o Render usa o nome do serviço quando
   ele está livre. Se não estiver, ele acrescenta um sufixo e você corrige
   no passo 4. O `JWT_SECRET` é gerado sozinho pelo Render.
5. Clique em **Apply**. O primeiro deploy leva alguns minutos (a API
   instala as dependências Python; o site roda `npm ci` e o build).

---

## 4. Conferir as URLs e acertar as variáveis

Quando os dois serviços estiverem **Live**, abra cada um no painel e
copie a URL que aparece no topo (ex.: `https://voluntiva-api-x1y2.onrender.com`).

Se alguma for diferente do palpite do passo 3:

- **voluntiva-api > Environment**: ajuste `CORS_ORIGINS` para a URL exata
  do site, **sem barra no final**, e salve. A API reinicia sozinha. Para
  liberar mais de uma origem, separe por vírgula.
- **voluntiva-web > Environment**: ajuste `VITE_API_URL` para a URL exata
  da API e salve com **Save, rebuild, and deploy**. Variáveis `VITE_`
  entram no JavaScript na hora do build, então só valem depois de um
  novo deploy do site.

Se você criar um domínio próprio depois, inclua-o também em `CORS_ORIGINS`.

---

## 5. Testar

1. Abra `https://<sua-api>.onrender.com/health`. Esperado:
   `{"status":"ok","banco":"ok","ambiente":"production"}`.
   Se aparecer `"banco":"indisponivel"`, revise a `DATABASE_URL`.
2. Abra o site, crie uma conta de voluntário e uma de ONG pela tela de
   cadastro e entre com elas. (O Swagger em `/docs` fica desligado em
   produção, de propósito.)
3. Teste o tempo real: com a ONG, crie uma ação; com o voluntário, faça a
   inscrição e veja a notificação chegar no sino sem recarregar. No
   navegador, **F12 > Network > WS** deve mostrar
   `wss://<sua-api>.onrender.com/ws/notificacoes` com status **101**.
4. Recarregue a página numa rota interna (ex.: `/acoes`). Ela deve abrir
   normalmente (regra de rewrite do `render.yaml`).

Dica para a apresentação: crie as contas e algumas ações de exemplo
antes do dia, para não depender de cadastro ao vivo.

---

## 6. Manter a API acordada com o UptimeRobot

No plano Free, o Render desliga a API depois de **15 minutos sem
requisições**, e a primeira requisição seguinte espera cerca de 50
segundos até ela voltar. Para evitar isso durante as duas semanas, um
monitor externo gratuito chama o `/health` a cada 10 minutos.

1. Crie uma conta gratuita em https://uptimerobot.com.
2. **New monitor**:
   - Tipo: **HTTP(s)**
   - URL: `https://<sua-api>.onrender.com/health`
   - Intervalo: **10 minutos** (qualquer valor abaixo de 15 serve; o
     mínimo do plano gratuito é 5)
3. Salve. Em poucos minutos o monitor fica verde (**Up**).

Por que cabe no plano gratuito: as 750 horas mensais do Render bastam
para um serviço ligado o mês inteiro (30 × 24 = 720 h), e só a API
consome horas (o Static Site não dorme nem conta horas). Bônus: cada
ping roda um `SELECT 1`, então o Supabase não pausa por inatividade.

Alternativa ao UptimeRobot, também gratuita: https://cron-job.org com
um job a cada 10 minutos para a mesma URL.

Depois da apresentação, pause o monitor para a API voltar a dormir.

---

## 7. Servidor VAP no notebook (só para a demo do protocolo)

O VAP roda localmente apontando para o mesmo Supabase. No `.env` da raiz
do repositório (nunca versionado), use a mesma `DATABASE_URL` do Render e
o **mesmo `JWT_SECRET`** que o Render gerou (copie em
**voluntiva-api > Environment**). Assim um token obtido no site também
vale no VAP, e vice-versa.

```powershell
cd backend
.venv\Scripts\python -m protocol
```

O servidor escuta em `localhost:5050`. O roteiro de comandos está em
`docs/GUIA_EXECUCAO.md` e a especificação em `docs/VAP.md`. Notificações
geradas por comandos VAP ficam gravadas no banco e aparecem no site na
próxima carga da página (o WebSocket vive no processo da API).

---

## 8. Problemas comuns

| Sintoma | Causa provável | O que fazer |
| --- | --- | --- |
| Deploy da API falha com `DATABASE_URL deve usar o driver psycopg3` | faltou o `+psycopg` | comece a URL com `postgresql+psycopg://` |
| Deploy da API falha com `Network is unreachable` ou timeout no banco | conexão direta (IPv6) do Supabase | use o **Session pooler**, porta 5432 |
| `password authentication failed for user "voluntiva_app..."` | senha errada ou não definida | refaça o passo 1.2; senha com `@ : / ?` precisa de URL-encode |
| Login falha e o console do navegador mostra erro de **CORS** | `CORS_ORIGINS` não bate com a URL do site | URL exata, com `https://` e sem `/` no final |
| Site chama `/api/v1/...` no próprio domínio do site e dá 404 | `VITE_API_URL` vazio ou build antigo | defina a variável e faça **rebuild and deploy** do site |
| Sino não atualiza em tempo real | WebSocket bloqueado ou API dormindo | confira a aba **WS** (status 101); o cliente reconecta sozinho |
| Primeira abertura demora ~1 minuto | a API estava dormindo | configure o UptimeRobot (seção 6) |
| `/health` mostra `"banco":"indisponivel"` | Supabase pausado ou URL errada | em Supabase, **Restore project** se estiver pausado |
| Console mostra `Refused to connect ... Content Security Policy` | a API está fora de `*.onrender.com` (domínio próprio) | acrescente o domínio em `connect-src` no header CSP do `render.yaml` |
| Login responde **429** | 10 senhas erradas seguidas para o mesmo e-mail | espere 15 minutos (ou reinicie a API); ver `docs/SECURITY.md` |

Logs: **voluntiva-api > Logs** no painel do Render.

---

## 9. Depois da apresentação

Nada gera cobrança, mas para encerrar: pause o monitor do UptimeRobot e,
no Render, use **Settings > Suspend** (ou **Delete**) em cada serviço.
O projeto do Supabase pode ficar como está; ele só pausa sozinho depois
de uma semana sem acesso.
