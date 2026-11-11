# Integração frontend ↔ API — 11/11/2026

## O que está ligado a dados reais

A aplicação carregada em `src/App.jsx` agora monta `src/RealApp.jsx`, que **não importa `servico.js` nem inicializa o mock localStorage**. Há fluxos para:

- Sessão via `POST /api/v1/auth/login` e `GET /api/v1/auth/eu`;
- Cadastro de voluntário via `POST /api/v1/auth/registro` (senha mínima de 8 caracteres);
- Catálogo de ações publicadas e detalhe individual via `GET /api/v1/acoes`;
- Inscrição, cancelamento e histórico do próprio usuário via `/api/v1/inscricoes`;
- Consulta de ONGs do gestor via `GET /api/v1/ongs/minhas`;
- Criação/publicação e cancelamento de ações pela ONG vinculada.

`frontend/src/lib/api.ts` mantém a camada HTTP centralizada. JWT ainda está em localStorage: aceitável **apenas para protótipo local**, não para publicação pública.

## Como executar em desenvolvimento

1. Aplicar `db/migrations/0001_voluntiva_schema.sql` e `0002_codigo_publico_acao.sql` em um banco PostgreSQL **de desenvolvimento**.
2. Na raiz, criar `.env` a partir de `.env.example`, com `DATABASE_URL` válido (driver `postgresql+psycopg://`) e `JWT_SECRET` de ao menos 32 caracteres.
3. Executar no backend: `pip install -r requirements-dev.txt` e `uvicorn app.main:app --reload --port 8000`.
4. Executar no frontend: `npm ci` e `npm run dev`; abrir `http://localhost:5173`.
5. Conferir `http://localhost:8000/health` e a aba Network do navegador. A UI **não** precisa mais de contas de teste mock.

`frontend/nginx.conf` encaminha `/api` e `/ws` para o hostname `backend` (nome esperado em rede Docker). Hospedagem estática separada precisa de proxy equivalente.

## Limites conhecidos

- O backend **não oferece cadastro público de ONGs**. Contas do tipo ONG, seus vínculos `ong_membro` e unidades precisam ser cadastrados pela equipe; a interface não simula essa função.
- A interface MVP substitui temporariamente telas mais avançadas do protótipo anterior. Ainda faltam: edição de ações, unidades, notificações, perfil/compatibilidade RF004, histórico detalhado de presença e fluxos visuais de check-in/check-out.
- Catálogo inicial consulta até 100 ações. Paginação completa ainda não está implementada no frontend.
- Ações criadas inicialmente como rascunho são publicadas em uma segunda requisição. Falha nesta segunda etapa deixa o rascunho persistido; o painel permite publicar depois.
- Cadastro/consulta de voluntários não gera automaticamente dados de ONG.
- Não houve execução de `npm run build`, `npm run lint`, `npm run typecheck`, `pytest` nem teste com Supabase nesta sessão; é obrigatório executá-los antes de merge.
- A antiga UI mock continua no repositório como referência, mas não é usada no ponto de entrada.

## Smoke test de integração

- [ ] Registrar voluntário com senha de pelo menos 8 caracteres
- [ ] Fazer logout, login e recarregar página, mantendo sessão válida
- [ ] Ver listagem de ação publicada do banco
- [ ] Inscrever-se, conferir banco, recarregar e cancelar inscrição
- [ ] Fazer login com usuário ONG associado em `ong_membro`
- [ ] Criar ação, publicar e conferi-la no catálogo
- [ ] Tentar editar/cancelar ação de outra ONG → HTTP 403
- [ ] Inspecionar Network: todas as operações vêm de `/api/v1`, sem dados-semente
- [ ] Executar build/lint/typecheck do frontend e pytest do backend
