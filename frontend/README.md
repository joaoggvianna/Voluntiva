# Frontend — Voluntiva

Interface React 18 + Vite 5 + Tailwind 3.

## Estado da integração (11/11/2026)

A entrada `src/App.jsx` monta `src/RealApp.jsx`, que utiliza somente o cliente REST `src/lib/api.ts` e o FastAPI. A interface ativa **não usa os dados mockados** de `src/data/` nem `src/lib/servico.js`.

Fluxos implementados na interface ativa:
- Cadastro e autenticação de voluntários;
- Consulta de ações publicadas e detalhes;
- Inscrição/cancelamento e listagem de inscrições próprias;
- Consulta de ONGs às quais o gestor está vinculado;
- Criação, publicação e cancelamento de ações da ONG.

O código da interface mock original foi mantido como referência para implementação futura de funcionalidades não cobertas pelo MVP real. **Não se deve apresentar as funcionalidades mock como entregues.**

### Rodando

```bash
npm ci
npm run dev
npm run build
npm run lint
npm run typecheck
```

O proxy do Vite encaminha `/api` ao FastAPI em `http://localhost:8000`. Configure `frontend/.env.local` somente se a API estiver em endereço diferente. Para execução com Nginx, `frontend/nginx.conf` pressupõe o hostname Docker `backend`.

**Limitações de segurança:** JWT ainda é persistido em `localStorage` no protótipo acadêmico. Não exponha a usuários reais sem migrar a sessão para cookie `httpOnly` e HTTPS. Cadastro de ONG, unidades, gerenciamento de presença, notificações e filtro RF004 ainda exigem endpoints/telas adicionais.

Veja [documentação de integração](../docs/INTEGRACAO_FRONTEND.md) para contratos, execução e checklist de validação.
