-- =====================================================================
-- Voluntiva — Sistema de Gestão de Voluntários para ONGs
-- Migration 0001: schema relacional inicial
--
-- Alvo: PostgreSQL 15+ (Supabase)
-- Aplicar em: SQL Editor do projeto Voluntiva-Proj
--
-- Convenções:
--   * nomes em snake_case, singular, português
--   * PK uuid (gen_random_uuid(), nativo no PG13+; não precisa de pgcrypto)
--   * todo instante de tempo é timestamptz (nunca timestamp sem fuso)
--   * ON DELETE RESTRICT no que é histórico; CASCADE só em tabelas-filhas
--   * RLS habilitado em tudo, sem policy permissiva = negado por padrão
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. Tipos enumerados
-- Enum em vez de VARCHAR + CHECK: o valor inválido vira erro de tipo,
-- e o conjunto fica documentado no catálogo do banco.
-- ---------------------------------------------------------------------

create type public.tipo_usuario as enum ('voluntario', 'ong', 'admin');

create type public.papel_membro as enum ('proprietario', 'gestor', 'operador');

create type public.nivel_habilidade as enum ('basico', 'intermediario', 'avancado');

create type public.status_acao as enum (
  'rascunho', 'publicada', 'em_andamento', 'concluida', 'cancelada'
);

create type public.status_inscricao as enum (
  'pendente', 'confirmada', 'lista_espera', 'cancelada'
);

create type public.tipo_notificacao as enum (
  'acao_criada', 'acao_atualizada', 'acao_cancelada',
  'inscricao_confirmada', 'inscricao_cancelada', 'lembrete'
);

-- ---------------------------------------------------------------------
-- 2. Função utilitária: manutenção de atualizado_em
--
-- SET search_path = '' + nomes qualificados: sem isso um schema malicioso
-- no search_path do chamador poderia sequestrar a resolução de nomes
-- dentro da função. É o que o linter do Supabase cobra.
-- ---------------------------------------------------------------------

create or replace function public.fn_set_atualizado_em()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.atualizado_em := now();
  return new;
end;
$$;

comment on function public.fn_set_atualizado_em() is
  'Trigger BEFORE UPDATE: mantém atualizado_em sob controle do banco, não do cliente.';

-- ---------------------------------------------------------------------
-- 3. USUARIO — identidade de autenticação (comando LOGIN do protocolo)
--
-- SEGURANÇA: a coluna guarda o HASH, nunca a senha. O servidor TCP deve
-- usar Argon2id (preferível) ou bcrypt com cost >= 12. O banco não
-- calcula nem valida hash — não existe função de senha aqui de propósito,
-- para que uma eventual injeção de SQL não vire um oráculo de senhas.
-- ---------------------------------------------------------------------

create table public.usuario (
  id             uuid primary key default gen_random_uuid(),
  email          text        not null,
  senha_hash     text        not null,
  nome           text        not null,
  tipo           public.tipo_usuario not null,
  ativo          boolean     not null default true,
  ultimo_login   timestamptz,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),

  constraint usuario_email_formato_chk
    check (email ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
  constraint usuario_email_tamanho_chk
    check (char_length(email) between 5 and 320),
  constraint usuario_nome_chk
    check (char_length(btrim(nome)) between 2 and 120),
  -- barreira contra gravar senha em claro por engano: nenhum hash moderno
  -- é curto, e todos começam com $ (formato PHC/modular crypt)
  constraint usuario_senha_hash_chk
    check (char_length(senha_hash) >= 20 and senha_hash like '$%')
);

-- unicidade case-insensitive sem depender da extensão citext
create unique index usuario_email_uidx on public.usuario (lower(email));

comment on column public.usuario.senha_hash is
  'Hash Argon2id/bcrypt no formato PHC. NUNCA armazenar senha em texto claro.';

create trigger trg_usuario_atualizado_em
  before update on public.usuario
  for each row execute function public.fn_set_atualizado_em();

-- ---------------------------------------------------------------------
-- 4. VOLUNTARIO — perfil 1:1 com usuario
--
-- Não guardamos CPF: o escopo do projeto não exige e dado pessoal que
-- não é coletado não vaza (minimização de dados, art. 6º LGPD).
-- ---------------------------------------------------------------------

create table public.voluntario (
  id                uuid primary key default gen_random_uuid(),
  usuario_id        uuid not null unique
                    references public.usuario(id) on delete cascade,
  telefone          text,
  data_nascimento   date,
  cidade            text,
  uf                char(2),
  biografia         text,
  criado_em         timestamptz not null default now(),
  atualizado_em     timestamptz not null default now(),

  constraint voluntario_uf_chk       check (uf is null or uf ~ '^[A-Z]{2}$'),
  constraint voluntario_telefone_chk check (telefone is null or telefone ~ '^[0-9]{10,13}$'),
  constraint voluntario_bio_chk      check (biografia is null or char_length(biografia) <= 1000),
  -- voluntário menor de 16 exige tratamento legal específico; barramos no banco
  constraint voluntario_idade_minima_chk
    check (data_nascimento is null or data_nascimento <= current_date - interval '16 years')
);

create trigger trg_voluntario_atualizado_em
  before update on public.voluntario
  for each row execute function public.fn_set_atualizado_em();

-- ---------------------------------------------------------------------
-- 5. ONG
-- ---------------------------------------------------------------------

create table public.ong (
  id             uuid primary key default gen_random_uuid(),
  nome           text not null,
  cnpj           char(14),
  email_contato  text,
  telefone       text,
  descricao      text,
  site           text,
  ativo          boolean     not null default true,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),

  constraint ong_nome_chk  check (char_length(btrim(nome)) between 2 and 160),
  constraint ong_cnpj_chk  check (cnpj is null or cnpj ~ '^[0-9]{14}$'),
  constraint ong_email_chk check (email_contato is null or
                                  email_contato ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
  constraint ong_site_chk  check (site is null or site ~* '^https?://')
);

create unique index ong_cnpj_uidx on public.ong (cnpj) where cnpj is not null;

comment on column public.ong.cnpj is
  'Apenas dígitos. A validação do dígito verificador fica no servidor de aplicação.';

create trigger trg_ong_atualizado_em
  before update on public.ong
  for each row execute function public.fn_set_atualizado_em();

-- ---------------------------------------------------------------------
-- 6. UNIDADE — filial/local físico de uma ONG
-- ---------------------------------------------------------------------

create table public.unidade (
  id             uuid primary key default gen_random_uuid(),
  ong_id         uuid not null references public.ong(id) on delete cascade,
  nome           text not null,
  cep            char(8),
  logradouro     text,
  numero         text,
  complemento    text,
  bairro         text,
  cidade         text not null,
  uf             char(2) not null,
  ativo          boolean     not null default true,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),

  constraint unidade_nome_chk check (char_length(btrim(nome)) between 2 and 160),
  constraint unidade_uf_chk   check (uf ~ '^[A-Z]{2}$'),
  constraint unidade_cep_chk  check (cep is null or cep ~ '^[0-9]{8}$'),
  -- duas unidades da mesma ONG não podem ter o mesmo nome
  constraint unidade_nome_por_ong_uk unique (ong_id, nome)
);

create index unidade_ong_idx on public.unidade (ong_id);

create trigger trg_unidade_atualizado_em
  before update on public.unidade
  for each row execute function public.fn_set_atualizado_em();

-- ---------------------------------------------------------------------
-- 7. ONG_MEMBRO — quais usuários operam quais ONGs/unidades
--
-- É esta tabela que sustenta os três clientes do diagrama de arquitetura:
-- unidade_id NULL  -> login no escopo da ONG inteira  (Cliente ONG)
-- unidade_id != NULL -> login restrito a uma unidade  (Cliente Unidade)
-- Sem ela, a autorização viraria uma coluna solta em `ong` e não haveria
-- como um gestor responder por duas ONGs.
-- ---------------------------------------------------------------------

create table public.ong_membro (
  id          uuid primary key default gen_random_uuid(),
  usuario_id  uuid not null references public.usuario(id) on delete cascade,
  ong_id      uuid not null references public.ong(id)     on delete cascade,
  unidade_id  uuid          references public.unidade(id) on delete cascade,
  papel       public.papel_membro not null default 'operador',
  criado_em   timestamptz not null default now(),

  constraint ong_membro_uk unique (usuario_id, ong_id, unidade_id)
);

create index ong_membro_usuario_idx on public.ong_membro (usuario_id);
create index ong_membro_ong_idx     on public.ong_membro (ong_id);

-- garante que a unidade citada pertence de fato à ONG citada
create or replace function public.fn_valida_membro_unidade()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_ong_da_unidade uuid;
begin
  if new.unidade_id is null then
    return new;
  end if;

  select u.ong_id into v_ong_da_unidade
    from public.unidade u
   where u.id = new.unidade_id;

  if v_ong_da_unidade is distinct from new.ong_id then
    raise exception 'Unidade % não pertence à ONG %', new.unidade_id, new.ong_id
      using errcode = '23514';
  end if;

  return new;
end;
$$;

create trigger trg_ong_membro_valida_unidade
  before insert or update on public.ong_membro
  for each row execute function public.fn_valida_membro_unidade();

-- ---------------------------------------------------------------------
-- 8. HABILIDADE — catálogo controlado
-- ---------------------------------------------------------------------

create table public.habilidade (
  id         uuid primary key default gen_random_uuid(),
  nome       text not null,
  categoria  text,
  descricao  text,
  criado_em  timestamptz not null default now(),

  constraint habilidade_nome_chk check (char_length(btrim(nome)) between 2 and 80)
);

create unique index habilidade_nome_uidx on public.habilidade (lower(btrim(nome)));

-- ---------------------------------------------------------------------
-- 9. VOLUNTARIO_HABILIDADE — N:N
-- ---------------------------------------------------------------------

create table public.voluntario_habilidade (
  voluntario_id  uuid not null references public.voluntario(id) on delete cascade,
  habilidade_id  uuid not null references public.habilidade(id) on delete restrict,
  nivel          public.nivel_habilidade not null default 'basico',
  criado_em      timestamptz not null default now(),

  primary key (voluntario_id, habilidade_id)
);

create index voluntario_habilidade_hab_idx on public.voluntario_habilidade (habilidade_id);

-- ---------------------------------------------------------------------
-- 10. VOLUNTARIO_DISPONIBILIDADE — janelas semanais recorrentes
-- ---------------------------------------------------------------------

create table public.voluntario_disponibilidade (
  id             uuid primary key default gen_random_uuid(),
  voluntario_id  uuid not null references public.voluntario(id) on delete cascade,
  dia_semana     smallint not null,   -- 0 = domingo ... 6 = sábado (igual ao EXTRACT(DOW))
  hora_inicio    time not null,
  hora_fim       time not null,

  constraint disponibilidade_dia_chk    check (dia_semana between 0 and 6),
  constraint disponibilidade_ordem_chk  check (hora_fim > hora_inicio),
  constraint disponibilidade_uk unique (voluntario_id, dia_semana, hora_inicio, hora_fim)
);

create index disponibilidade_voluntario_idx
  on public.voluntario_disponibilidade (voluntario_id);

comment on column public.voluntario_disponibilidade.dia_semana is
  '0=domingo .. 6=sábado, mesma convenção de EXTRACT(DOW FROM data).';

-- ---------------------------------------------------------------------
-- 11. ACAO_SOCIAL — o evento (CREATE_EVENT / UPDATE_EVENT / LIST_EVENTS)
-- ---------------------------------------------------------------------

create table public.acao_social (
  id             uuid primary key default gen_random_uuid(),
  ong_id         uuid not null references public.ong(id)      on delete restrict,
  unidade_id     uuid          references public.unidade(id)  on delete set null,
  titulo         text not null,
  descricao      text,
  local_texto    text,
  inicio         timestamptz not null,
  fim            timestamptz not null,
  vagas          integer not null,
  status         public.status_acao not null default 'rascunho',
  criado_por     uuid references public.usuario(id) on delete set null,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),

  constraint acao_titulo_chk    check (char_length(btrim(titulo)) between 3 and 160),
  constraint acao_periodo_chk   check (fim > inicio),
  constraint acao_vagas_chk     check (vagas between 1 and 100000),
  constraint acao_descricao_chk check (descricao is null or char_length(descricao) <= 5000)
);

-- índices desenhados para as consultas reais do protocolo:
-- LIST_EVENTS filtra por status e ordena por data de início
create index acao_status_inicio_idx on public.acao_social (status, inicio);
create index acao_ong_idx           on public.acao_social (ong_id);
create index acao_unidade_idx       on public.acao_social (unidade_id)
  where unidade_id is not null;

create trigger trg_acao_atualizado_em
  before update on public.acao_social
  for each row execute function public.fn_set_atualizado_em();

-- unidade da ação precisa pertencer à ONG da ação
create or replace function public.fn_valida_acao_unidade()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_ong_da_unidade uuid;
begin
  if new.unidade_id is null then
    return new;
  end if;

  select u.ong_id into v_ong_da_unidade
    from public.unidade u
   where u.id = new.unidade_id;

  if v_ong_da_unidade is distinct from new.ong_id then
    raise exception 'Unidade % não pertence à ONG % da ação social',
      new.unidade_id, new.ong_id using errcode = '23514';
  end if;

  return new;
end;
$$;

create trigger trg_acao_valida_unidade
  before insert or update on public.acao_social
  for each row execute function public.fn_valida_acao_unidade();

-- ---------------------------------------------------------------------
-- 12. ACAO_HABILIDADE — competências pedidas pela ação
-- ---------------------------------------------------------------------

create table public.acao_habilidade (
  acao_id        uuid not null references public.acao_social(id) on delete cascade,
  habilidade_id  uuid not null references public.habilidade(id)  on delete restrict,
  obrigatoria    boolean not null default false,

  primary key (acao_id, habilidade_id)
);

create index acao_habilidade_hab_idx on public.acao_habilidade (habilidade_id);

-- ---------------------------------------------------------------------
-- 13. INSCRICAO — JOIN_EVENT / LEAVE_EVENT
--
-- A UNIQUE (acao_id, voluntario_id) é a restrição central do sistema:
-- impede inscrição duplicada mesmo sob concorrência, porque o índice
-- único é verificado dentro da transação, não pela aplicação.
-- ---------------------------------------------------------------------

create table public.inscricao (
  id                    uuid primary key default gen_random_uuid(),
  acao_id               uuid not null references public.acao_social(id) on delete cascade,
  voluntario_id         uuid not null references public.voluntario(id)  on delete restrict,
  status                public.status_inscricao not null default 'pendente',
  inscrito_em           timestamptz not null default now(),
  cancelado_em          timestamptz,
  motivo_cancelamento   text,

  constraint inscricao_uk unique (acao_id, voluntario_id),
  -- estado e carimbo de cancelamento não podem divergir
  constraint inscricao_cancelamento_chk check (
    (status = 'cancelada'  and cancelado_em is not null) or
    (status <> 'cancelada' and cancelado_em is null)
  ),
  constraint inscricao_motivo_chk
    check (motivo_cancelamento is null or char_length(motivo_cancelamento) <= 500)
);

create index inscricao_voluntario_idx on public.inscricao (voluntario_id);
create index inscricao_acao_status_idx on public.inscricao (acao_id, status);

-- ---------------------------------------------------------------------
-- 13.1 Controle de lotação — regra de negócio no banco
--
-- Por que aqui e não só no servidor: com N clientes TCP simultâneos, um
-- "SELECT count(*) ... IF < vagas THEN INSERT" na aplicação é uma race
-- condition clássica — duas conexões leem 9/10 e ambas inserem.
-- O SELECT ... FOR UPDATE serializa as transações que disputam a MESMA
-- ação, então a lotação nunca é ultrapassada. É exatamente o cenário do
-- "teste de concorrência" previsto no plano de ações.
-- ---------------------------------------------------------------------

create or replace function public.fn_valida_inscricao()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_vagas       integer;
  v_status_acao public.status_acao;
  v_confirmadas integer;
begin
  -- trava a linha da ação: concorrentes na mesma ação esperam aqui
  select a.vagas, a.status
    into v_vagas, v_status_acao
    from public.acao_social a
   where a.id = new.acao_id
     for update;

  if not found then
    raise exception 'Ação social % não encontrada', new.acao_id using errcode = '23503';
  end if;

  if v_status_acao in ('cancelada', 'concluida') then
    raise exception 'Não é possível inscrever-se em ação com status %', v_status_acao
      using errcode = '23514';
  end if;

  if new.status = 'confirmada' then
    select count(*)
      into v_confirmadas
      from public.inscricao i
     where i.acao_id = new.acao_id
       and i.status  = 'confirmada'
       and i.id <> new.id;

    if v_confirmadas >= v_vagas then
      raise exception 'Ação social % está lotada (% de % vagas)',
        new.acao_id, v_confirmadas, v_vagas using errcode = '23514';
    end if;
  end if;

  return new;
end;
$$;

create trigger trg_inscricao_valida
  before insert or update of status, acao_id on public.inscricao
  for each row execute function public.fn_valida_inscricao();

-- ---------------------------------------------------------------------
-- 14. PRESENCA — CHECK_IN / CHECK_OUT
--
-- PK = inscricao_id: garante no nível do schema uma presença por
-- inscrição, sem precisar de UNIQUE extra.
-- horas_computadas é GENERATED: não pode divergir dos carimbos.
-- ---------------------------------------------------------------------

create table public.presenca (
  inscricao_id      uuid primary key
                    references public.inscricao(id) on delete cascade,
  check_in          timestamptz not null,
  check_out         timestamptz,
  registrado_por    uuid references public.usuario(id) on delete set null,
  observacao        text,
  horas_computadas  numeric(6,2)
                    generated always as (
                      case
                        when check_out is null then null
                        else round(extract(epoch from (check_out - check_in))::numeric / 3600, 2)
                      end
                    ) stored,

  constraint presenca_ordem_chk      check (check_out is null or check_out > check_in),
  constraint presenca_observacao_chk check (observacao is null or char_length(observacao) <= 500)
);

-- presença só faz sentido para inscrição confirmada
create or replace function public.fn_valida_presenca()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_status public.status_inscricao;
begin
  select i.status into v_status
    from public.inscricao i
   where i.id = new.inscricao_id;

  if v_status is distinct from 'confirmada' then
    raise exception 'Presença exige inscrição confirmada (status atual: %)', v_status
      using errcode = '23514';
  end if;

  return new;
end;
$$;

create trigger trg_presenca_valida
  before insert or update on public.presenca
  for each row execute function public.fn_valida_presenca();

-- ---------------------------------------------------------------------
-- 15. NOTIFICACAO
-- ---------------------------------------------------------------------

create table public.notificacao (
  id          uuid primary key default gen_random_uuid(),
  usuario_id  uuid not null references public.usuario(id)     on delete cascade,
  acao_id     uuid          references public.acao_social(id) on delete cascade,
  tipo        public.tipo_notificacao not null,
  titulo      text not null,
  mensagem    text not null,
  lida        boolean not null default false,
  criada_em   timestamptz not null default now(),

  constraint notificacao_titulo_chk   check (char_length(btrim(titulo)) between 1 and 160),
  constraint notificacao_mensagem_chk check (char_length(mensagem) <= 2000)
);

-- índice parcial: a consulta quente é "não lidas deste usuário"
create index notificacao_nao_lidas_idx
  on public.notificacao (usuario_id, criada_em desc)
  where lida = false;

-- =====================================================================
-- 16. Views de consulta
--
-- security_invoker = true: a view roda com os privilégios de quem
-- consulta, não de quem criou. Sem isso a view seria um bypass de RLS
-- (é o alerta "Security Definer View" do linter do Supabase).
-- =====================================================================

create view public.vw_acao_vagas
  with (security_invoker = true)
as
select
  a.id                as acao_id,
  a.ong_id,
  o.nome              as ong_nome,
  a.unidade_id,
  a.titulo,
  a.inicio,
  a.fim,
  a.status,
  a.vagas,
  count(i.id) filter (where i.status = 'confirmada')  as vagas_ocupadas,
  a.vagas - count(i.id) filter (where i.status = 'confirmada') as vagas_disponiveis,
  count(i.id) filter (where i.status = 'lista_espera') as em_lista_espera
from public.acao_social a
join public.ong o on o.id = a.ong_id
left join public.inscricao i on i.acao_id = a.id
group by a.id, o.nome;

comment on view public.vw_acao_vagas is
  'Ocupação por ação social. Base para o LIST_EVENTS do protocolo.';

create view public.vw_historico_voluntario
  with (security_invoker = true)
as
select
  v.id            as voluntario_id,
  u.nome          as voluntario_nome,
  a.id            as acao_id,
  a.titulo        as acao_titulo,
  o.nome          as ong_nome,
  a.inicio,
  a.fim,
  i.status        as status_inscricao,
  p.check_in,
  p.check_out,
  p.horas_computadas
from public.voluntario v
join public.usuario    u on u.id = v.usuario_id
join public.inscricao  i on i.voluntario_id = v.id
join public.acao_social a on a.id = i.acao_id
join public.ong        o on o.id = a.ong_id
left join public.presenca p on p.inscricao_id = i.id;

comment on view public.vw_historico_voluntario is
  'Histórico de participação e horas por voluntário.';

-- =====================================================================
-- 17. Row Level Security
--
-- O servidor TCP conecta ao Postgres com um papel próprio (ver seção 18)
-- e faz a autorização na aplicação. Ainda assim habilitamos RLS em TODAS
-- as tabelas: no Supabase o schema `public` é exposto via PostgREST, e
-- uma tabela sem RLS ali fica legível por qualquer um com a chave
-- publishable/anon. Sem policy permissiva, o padrão é NEGAR.
--
-- FORCE: aplica RLS inclusive ao dono da tabela.
-- =====================================================================

alter table public.usuario                    enable row level security;
alter table public.voluntario                 enable row level security;
alter table public.ong                        enable row level security;
alter table public.unidade                    enable row level security;
alter table public.ong_membro                 enable row level security;
alter table public.habilidade                 enable row level security;
alter table public.voluntario_habilidade      enable row level security;
alter table public.voluntario_disponibilidade enable row level security;
alter table public.acao_social                enable row level security;
alter table public.acao_habilidade            enable row level security;
alter table public.inscricao                  enable row level security;
alter table public.presenca                   enable row level security;
alter table public.notificacao                enable row level security;

alter table public.usuario                    force row level security;
alter table public.voluntario                 force row level security;
alter table public.ong                        force row level security;
alter table public.unidade                    force row level security;
alter table public.ong_membro                 force row level security;
alter table public.habilidade                 force row level security;
alter table public.voluntario_habilidade      force row level security;
alter table public.voluntario_disponibilidade force row level security;
alter table public.acao_social                force row level security;
alter table public.acao_habilidade            force row level security;
alter table public.inscricao                  force row level security;
alter table public.presenca                   force row level security;
alter table public.notificacao                force row level security;

-- =====================================================================
-- 18. Privilégios
--
-- Revoga tudo dos papéis anônimos do Supabase. Nenhum cliente deve falar
-- com este banco pela API REST — só o servidor TCP fala, e ele usa um
-- papel dedicado. Os blocos são condicionais para o script rodar também
-- num Postgres local (onde esses papéis não existem).
-- =====================================================================

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    execute 'revoke all on all tables    in schema public from anon';
    execute 'revoke all on all sequences in schema public from anon';
    execute 'revoke all on all functions in schema public from anon';
    execute 'alter default privileges in schema public revoke all on tables from anon';
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    execute 'revoke all on all tables    in schema public from authenticated';
    execute 'revoke all on all sequences in schema public from authenticated';
    execute 'revoke all on all functions in schema public from authenticated';
    execute 'alter default privileges in schema public revoke all on tables from authenticated';
  end if;
end
$$;

-- ---------------------------------------------------------------------
-- Papel da aplicação (executar UMA vez, fora desta migration, trocando a
-- senha). Rodar o servidor como `postgres` ou `service_role` dá poder
-- muito além do necessário — este papel tem só DML, nada de DDL.
--
--   create role voluntiva_app with login password '<gerar-senha-forte>';
--   grant usage on schema public to voluntiva_app;
--   grant select, insert, update, delete
--     on all tables in schema public to voluntiva_app;
--   alter default privileges in schema public
--     grant select, insert, update, delete on tables to voluntiva_app;
--
-- E no servidor: SEMPRE queries parametrizadas ($1, $2...), nunca
-- concatenação de string — o LOGIN é o alvo óbvio de SQL injection.
-- ---------------------------------------------------------------------

-- =====================================================================
-- 19. Seed mínimo do catálogo de habilidades
-- =====================================================================

insert into public.habilidade (nome, categoria) values
  ('Ensino e reforço escolar', 'Educação'),
  ('Primeiros socorros',       'Saúde'),
  ('Cozinha e alimentação',    'Operacional'),
  ('Logística e estoque',      'Operacional'),
  ('Comunicação e redes sociais', 'Comunicação'),
  ('Design gráfico',           'Comunicação'),
  ('Desenvolvimento de software', 'Tecnologia'),
  ('Suporte técnico',          'Tecnologia'),
  ('Captação de recursos',     'Administrativo'),
  ('Direção de veículos',      'Operacional'),
  ('Libras',                   'Acessibilidade'),
  ('Cuidado com animais',      'Meio ambiente')
on conflict do nothing;

commit;
