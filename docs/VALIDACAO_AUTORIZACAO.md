# Checklist de validação — autorização (branch de correção)

Este patch restringe **operações REST de gestão** de ações e presença. Não conclui a migração do frontend nem a segurança de produção.

## Preparação

1. Aplicar as migrations `db/migrations/` em PostgreSQL de teste.
2. Criar duas ONGs (A e B), com unidades diferentes.
3. Criar usuário ONG vinculado apenas a A via `ong_membro`, usuário voluntário e usuário admin.
4. Iniciar API com `DATABASE_URL` e `JWT_SECRET` válidos.

## Testes automatizados

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_autorizacao.py -q
python -m pytest -q
```

## Verificações de integração manuais

- [ ] Perfil de ONG A cria ação em A: sucesso.
- [ ] Perfil de ONG A tenta criar ação em B: **403**.
- [ ] Perfil de ONG A tenta atualizar ação de B: **403**.
- [ ] Perfil de ONG A tenta criar ação apontando unidade de B: **422**.
- [ ] Perfil voluntário tenta criar/editar ação: **403**.
- [ ] Perfil voluntário tenta registrar check-in ou check-out: **403**.
- [ ] Perfil de ONG A tenta registrar presença na ação de B: **403**.
- [ ] Perfil de ONG A registra presença em ação de A: fluxo permitido.
- [ ] Perfil vinculado apenas à unidade A1 tenta gerir ação na A2: **403**.
- [ ] Admin realiza operação autorizada independente de vínculo.

## Pendências que devem bloquear publicação

- Integrar `frontend/src/lib/api.ts` às páginas; hoje a UI persiste mock em `localStorage`.
- Validar permissões equivalentes para futuros comandos de escrita VAP.
- Verificar autorização de cada endpoint novo (negação por padrão).
- Substituir armazenamento de JWT no navegador por sessão segura antes de exposição pública.
- Executar suíte automatizada e fluxos reais com Postgres; estes testes não foram executados pelo assistente no ambiente remoto.
