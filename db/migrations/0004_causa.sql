-- =====================================================================
-- Voluntiva — Migration 0004
-- Causa social de ONGs e ações
--
-- MOTIVO
--   A interface filtra e exibe ONGs e ações por causa (Educação, Saúde,
--   Animais...), mas o schema não tinha onde guardar isso.
--
--   Enum (como os demais do schema) em vez de texto livre: o filtro
--   depende de valores exatos, e o conjunto fica documentado no catálogo.
--   A interface traduz cada valor para o rótulo exibido.
--
--   Coluna NULL: ONGs e ações já cadastradas ficam "sem causa" até
--   alguém editar; nada é inventado no backfill.
--
--   ATENÇÃO: o DER e o voluntiva_mysql.sql da entrega precisam ganhar
--   a mesma coluna (no MySQL, ENUM(...) com os mesmos valores).
--
-- Idempotente: pode ser reaplicada sem erro.
-- =====================================================================

begin;

do $$
begin
  if not exists (select 1 from pg_type where typname = 'causa_social') then
    create type public.causa_social as enum (
      'meio_ambiente', 'educacao', 'animais', 'saude',
      'assistencia_social', 'cultura', 'esporte', 'direitos_humanos'
    );
  end if;
end
$$;

alter table public.ong         add column if not exists causa public.causa_social;
alter table public.acao_social add column if not exists causa public.causa_social;

-- Listagem pública de ações filtra por status + causa.
create index if not exists acao_causa_idx
  on public.acao_social (causa, inicio)
  where causa is not null;

comment on column public.ong.causa is 'Causa principal da ONG.';
comment on column public.acao_social.causa is
  'Causa da ação. Ao criar pela API, o padrão é a causa da ONG.';

commit;
