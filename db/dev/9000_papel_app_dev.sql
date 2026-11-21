-- =====================================================================
-- SOMENTE DESENVOLVIMENTO LOCAL (docker compose / CI).
--
-- Dá login ao papel voluntiva_app (criado sem login pela migration 0003)
-- com uma senha conhecida, para o backend do compose conectar com o papel
-- da aplicação e as policies de RLS valerem de verdade.
--
-- NUNCA aplicar no Supabase: lá a senha é gerada e guardada fora do repo.
-- =====================================================================

alter role voluntiva_app with login password 'voluntiva_app_dev';
