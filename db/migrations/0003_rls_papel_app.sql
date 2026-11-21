-- =====================================================================
-- Voluntiva — Migration 0003
-- Policies de RLS para o papel da aplicação + limite de vagas no banco
--
-- MOTIVO
--   A 0001 liga e FORÇA RLS em todas as tabelas e não cria nenhuma
--   policy. Sem policy, o padrão é negar: o papel voluntiva_app, que a
--   própria 0001 recomenda para o backend, veria zero linhas e toda
--   escrita falharia. Hoje o backend só funciona porque conecta como
--   `postgres`, que ignora RLS — poder muito além do necessário.
--
-- O QUE ESTA MIGRATION FAZ
--   1. Cria o papel voluntiva_app (se ainda não existir), sem senha.
--   2. Concede a ele só DML (nada de DDL) e uso das sequências.
--   3. Cria, em cada tabela, uma policy que libera tudo para
--      voluntiva_app. A autorização fina (quem pode ver/alterar o quê)
--      continua na aplicação: app/api/autorizacao.py.
--      anon e authenticated seguem SEM policy, ou seja, bloqueados.
--   4. Trigger que impede reduzir `vagas` abaixo das inscrições
--      confirmadas (o service também valida; o banco é a última barreira).
--
-- DEPOIS DE APLICAR (uma vez, fora do controle de versão):
--   alter role voluntiva_app with login password '<gerar-senha-forte>';
--   E trocar o DATABASE_URL do backend para esse usuário. No Supabase,
--   pelo pooler, o usuário fica no formato voluntiva_app.<project_ref>.
--
-- Idempotente: pode ser reaplicada sem erro.
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. Papel da aplicação
-- ---------------------------------------------------------------------

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'voluntiva_app') then
    -- NOLOGIN até alguém definir a senha: um papel com login e sem senha
    -- conhecida é inútil, e senha em migration versionada é vazamento.
    create role voluntiva_app nologin;
  end if;
end
$$;

-- ---------------------------------------------------------------------
-- 2. Privilégios: só DML
-- ---------------------------------------------------------------------

grant usage on schema public to voluntiva_app;
grant select, insert, update, delete on all tables in schema public to voluntiva_app;
grant usage, select on all sequences in schema public to voluntiva_app;

alter default privileges in schema public
  grant select, insert, update, delete on tables to voluntiva_app;
alter default privileges in schema public
  grant usage, select on sequences to voluntiva_app;

-- ---------------------------------------------------------------------
-- 3. Policies
--
-- Uma policy "for all" por tabela, restrita ao papel voluntiva_app.
-- As views (vw_acao_vagas, vw_historico_voluntario) são security_invoker,
-- então herdam estas policies ao serem consultadas pelo backend.
-- ---------------------------------------------------------------------

do $$
declare
  t text;
begin
  foreach t in array array[
    'usuario', 'voluntario', 'ong', 'unidade', 'ong_membro', 'habilidade',
    'voluntario_habilidade', 'voluntario_disponibilidade', 'acao_social',
    'acao_habilidade', 'inscricao', 'presenca', 'notificacao'
  ]
  loop
    execute format('drop policy if exists %I on public.%I', t || '_app_all', t);
    execute format(
      'create policy %I on public.%I as permissive for all to voluntiva_app '
      'using (true) with check (true)',
      t || '_app_all', t
    );
  end loop;
end
$$;

-- ---------------------------------------------------------------------
-- 4. Vagas nunca abaixo das inscrições confirmadas
--
-- Trava a mesma linha que fn_valida_inscricao trava (a da ação), então
-- uma edição de vagas e uma inscrição concorrentes se serializam.
-- ---------------------------------------------------------------------

create or replace function public.fn_valida_vagas_acao()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_confirmadas integer;
begin
  if new.vagas >= old.vagas then
    return new;
  end if;

  select count(*)
    into v_confirmadas
    from public.inscricao i
   where i.acao_id = new.id
     and i.status  = 'confirmada';

  if new.vagas < v_confirmadas then
    raise exception 'Ação social % tem % inscrições confirmadas; vagas não pode ser %',
      new.id, v_confirmadas, new.vagas using errcode = '23514';
  end if;

  return new;
end;
$$;

drop trigger if exists trg_acao_valida_vagas on public.acao_social;

create trigger trg_acao_valida_vagas
  before update of vagas on public.acao_social
  for each row execute function public.fn_valida_vagas_acao();

commit;
