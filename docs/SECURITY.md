# Segurança do Voluntiva

Estado das proteções da API, da interface web, do banco e do servidor VAP,
e o que ainda falta. Última revisão: novembro de 2026, com o deploy no
Render + Supabase já no ar.

Esta revisão não é uma auditoria independente nem garante ausência de
vulnerabilidades.

## 1. Segredos

- Nenhum segredo real no repositório nem no histórico do git (conferido
  em todos os commits). `.env` e `.env.*` estão no `.gitignore`; só os
  `.env.example`, com placeholders, são versionados.
- Em produção, `JWT_SECRET` é gerado pelo Render (`generateValue`) e
  `DATABASE_URL` é digitada no painel (`sync: false` no `render.yaml`).
- A API recusa subir com `JWT_SECRET` curto (menos de 32 caracteres) ou
  com o placeholder do `.env.example`.
- **`db/dev/` é só para desenvolvimento.** A senha do papel
  `voluntiva_app` (`voluntiva_app_dev`) e a senha das contas do seed
  (`voluntiva123`) são públicas. Esses arquivos nunca devem ser aplicados
  no Supabase. Na revisão de novembro de 2026 não havia nenhuma conta do
  seed no banco de produção.
- O Postgres do Docker Compose usa senhas públicas e por isso só escuta
  em `127.0.0.1:5433`.

## 2. Autenticação (API REST)

- Senhas com Argon2id (`argon2-cffi`). O banco não calcula hash.
- No máximo `ARGON2_MAX_SIMULTANEOS` (padrão 2) hashes ao mesmo tempo:
  cada hash aloca 64 MB, e sem esse teto uma rajada de logins derrubaria
  a instância gratuita do Render (512 MB) por falta de memória.
- Login com a mesma mensagem para e-mail inexistente e senha errada, e
  com o mesmo custo de tempo, para não permitir enumerar contas.
- **Limite de tentativas:** depois de `LOGIN_MAX_FALHAS` (10) falhas para
  o mesmo e-mail em `LOGIN_JANELA_SEGUNDOS` (15 minutos), o login responde
  `429` até a janela passar. A contagem é por e-mail, não por IP, porque
  atrás do proxy do Render o IP vem de um cabeçalho que o cliente pode
  forjar. Fica em memória: vale para uma instância e zera no restart.
- JWT HS256 com `exp` e `sub` obrigatórios e `scope` conferido: um
  refresh token não serve como access token e vice-versa.
- A cada requisição o usuário é relido do banco: conta desativada perde o
  acesso na hora.
- Respostas de `/api/v1/auth/*` vão com `Cache-Control: no-store`.

## 3. Autorização

Regras em `app/services/permissao.py`, compartilhadas pela API e pelo VAP,
e traduzidas para HTTP em `app/api/autorizacao.py`. Roteiro de conferência
em [VALIDACAO_AUTORIZACAO.md](VALIDACAO_AUTORIZACAO.md).

- Rotas de escrita exigem o tipo de usuário certo (`exigir_tipo`) e o
  vínculo com a ONG ou unidade (`exigir_acesso_ong`); só proprietário e
  gestor mexem na estrutura da ONG.
- Rascunhos só aparecem para membros da ONG.
- Notificações e inscrições são sempre filtradas pelo usuário do token.

## 4. WebSocket de notificações

- O token vai na **primeira mensagem** depois de abrir a conexão, e não
  na URL: a URL do handshake fica gravada no log de acesso do servidor e
  do proxy. Sem token válido em 10 segundos, a conexão é fechada (1008).
- A conta precisa estar ativa no banco, como na API REST.
- Em produção a conexão é sempre `wss://`.

## 5. HTTP: CORS e cabeçalhos

- CORS só para as origens de `CORS_ORIGINS` (em produção, o site do
  Render). Origem desconhecida recebe 400 no preflight.
- A API devolve `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
  e `Referrer-Policy: no-referrer`. Em produção `/docs` e `/openapi.json`
  ficam desligados.
- O site estático (headers no `render.yaml`) devolve HSTS (do próprio
  Render), `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` e uma
  **Content-Security-Policy** que só aceita scripts do próprio site e
  conexões para `*.onrender.com`. Se a API ganhar domínio próprio, inclua
  o domínio em `connect-src`.

## 6. Banco (Supabase)

- A API conecta como `voluntiva_app`: sem superusuário, sem `BYPASSRLS`,
  só DML (migration 0003).
- RLS ligado e forçado em todas as tabelas. As policies liberam só
  `voluntiva_app`; `anon` e `authenticated` (a API REST automática do
  Supabase) não têm policy nem grant nas tabelas, então não leem nada.
- Consultas sempre parametrizadas. Os poucos trechos de SQL montados com
  `format`/f-string só recebem expressões fixas do código, nunca dados do
  usuário. A busca textual escapa `%` e `_`.
- `statement_timeout` de 30 s e `idle_in_transaction_session_timeout` de
  60 s em cada conexão.

## 7. Servidor VAP (TCP)

Roda só localmente, para a demonstração do protocolo; não é publicado no
Render.

- Não há senha no protocolo: o cliente faz login pela API e envia o JWT no
  comando `AUTH`. O servidor valida o token e confere no banco se a conta
  segue ativa.
- `VAP_HOST` padrão é `127.0.0.1`. Use `0.0.0.0` só dentro do container
  ou para a demo em rede local.
- Framing com limites: cabeçalho até 8192 bytes, corpo até
  `VAP_MAX_MESSAGE_SIZE` (65536), `CONTENT-LENGTH` obrigatório, cabeçalhos
  duplicados recusados, JSON com profundidade máxima 32. Erro de framing
  encerra a conexão.
- Limites por processo: `VAP_MAX_CONNECTIONS` (64), por IP (8),
  requisições por conexão (1000) e por segundo (50), e 3 falhas de `AUTH`
  por conexão. Prazos para autenticar, para ler uma mensagem (30 s) e para
  escrever (5 s).
- TLS opcional (`VAP_USE_TLS`); o cliente de desenvolvimento **não**
  verifica o certificado.

## 8. Dependências

Na revisão de novembro de 2026:

- Python (`pip-audit`): sem vulnerabilidades conhecidas depois de subir
  `python-multipart` para 0.0.31 e `PyJWT` para 2.15.0.
- npm: `npm audit fix` resolveu as falhas com correção compatível. Restam
  duas que exigem trocar de versão maior:
  - `vite` 5 / `esbuild`: afeta só o servidor de desenvolvimento
    (`npm run dev`), não o site publicado. Correção: migrar para Vite 6+.
  - `react-router-dom` 6: open redirect quando a aplicação passa uma URL
    vinda do usuário para `<Link>`/`navigate`. A interface não faz isso
    hoje. Correção: migrar para React Router 7.

## 9. Pendências conhecidas

- **Função `rls_auto_enable` exposta no Supabase.** É criada pelo painel
  do Supabase (opção de ligar RLS automaticamente) como `SECURITY DEFINER`
  e pode ser chamada por `anon` em `/rest/v1/rpc/rls_auto_enable`. Não faz
  parte das migrations. Para fechar, rode no SQL Editor:

  ```sql
  revoke execute on function public.rls_auto_enable() from anon, authenticated, public;
  ```

- **Tokens em `localStorage`.** Um XSS consegue lê-los; a CSP reduz esse
  risco, mas o correto é cookie `httpOnly` + `SameSite` definido pelo
  backend.
- **Refresh token sem revogação.** Vale até expirar (7 dias); desativar a
  conta corta o acesso.
- **Sem limite de requisições geral na API.** Só o login é limitado.
  Cadastro e refresh não são; para isso o caminho é um limitador na borda
  (Cloudflare) ou um contador compartilhado.
- **Estado em memória.** O limite de login e as conexões WebSocket ficam
  no processo; com mais de uma instância precisam de Redis ou do banco.
- **TLS do VAP** sem verificação de certificado no cliente.
