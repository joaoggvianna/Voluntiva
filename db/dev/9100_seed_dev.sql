-- =====================================================================
-- Seed de DESENVOLVIMENTO: contas, ONGs, unidades, ações e inscrições
-- para demonstrar o sistema. Aplicado pelo docker compose depois das
-- migrations (ordem alfabética em /docker-entrypoint-initdb.d).
--
-- Todas as contas usam a senha:  voluntiva123
--   admin@voluntiva.dev        administrador
--   ong@voluntiva.dev          proprietária da ONG "Instituto Raízes"
--   operador@voluntiva.dev     operador só da unidade Barreiro
--   ong2@voluntiva.dev         proprietária da ONG "Patas Unidas"
--   voluntario@voluntiva.dev   voluntária com habilidades e disponibilidade
--   voluntario2@voluntiva.dev  voluntário sem perfil preenchido
--
-- Datas das ações são relativas ao dia em que o banco foi criado, para a
-- demonstração sempre ter ações futuras. A ação "Oficina de culinária"
-- tem 1 vaga: serve para mostrar a disputa pela última vaga entre dois
-- clientes (REST ou VAP).
--
-- NUNCA aplicar no Supabase de produção.
-- =====================================================================

begin;

-- Instante local (America/Sao_Paulo) daqui a `dias` dias, na hora `h`.
create function pg_temp.quando(dias int, h time) returns timestamptz
language sql stable as $$
  select ((date_trunc('day', now() at time zone 'America/Sao_Paulo')
           + make_interval(days => dias)) + h) at time zone 'America/Sao_Paulo'
$$;

-- ---------------------------------------------------------------------
-- Contas (hash Argon2id de "voluntiva123")
-- ---------------------------------------------------------------------
insert into public.usuario (id, email, senha_hash, nome, tipo) values
  ('00000000-0000-4000-8000-000000000001', 'admin@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Administração Voluntiva', 'admin'),
  ('00000000-0000-4000-8000-000000000002', 'ong@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Marina Souza', 'ong'),
  ('00000000-0000-4000-8000-000000000003', 'operador@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Paulo Lima', 'ong'),
  ('00000000-0000-4000-8000-000000000004', 'ong2@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Rita Alves', 'ong'),
  ('00000000-0000-4000-8000-000000000005', 'voluntario@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Ana Clara Ribeiro', 'voluntario'),
  ('00000000-0000-4000-8000-000000000006', 'voluntario2@voluntiva.dev',
   '$argon2id$v=19$m=65536,t=3,p=4$+A5fsbJamaGGe3sQACXcDw$N7cs7Azvs09ba5DyDwjkoK14kLFmIupLMav+BJKBUBw',
   'Bruno Costa', 'voluntario')
on conflict do nothing;

insert into public.voluntario (id, usuario_id, telefone, cidade, uf, biografia) values
  ('00000000-0000-4000-8000-000000000105', '00000000-0000-4000-8000-000000000005',
   '31988887777', 'Belo Horizonte', 'MG', 'Estudante de nutrição, gosto de cozinhar e organizar.'),
  ('00000000-0000-4000-8000-000000000106', '00000000-0000-4000-8000-000000000006',
   null, 'Contagem', 'MG', null)
on conflict do nothing;

-- Ana: cozinha e logística; disponível todos os dias das 06h às 18h.
insert into public.voluntario_habilidade (voluntario_id, habilidade_id, nivel)
select '00000000-0000-4000-8000-000000000105', id, 'intermediario'
  from public.habilidade
 where nome in ('Cozinha e alimentação', 'Logística e estoque')
on conflict do nothing;

insert into public.voluntario_disponibilidade (voluntario_id, dia_semana, hora_inicio, hora_fim)
select '00000000-0000-4000-8000-000000000105', d, '06:00', '18:00'
  from generate_series(0, 6) as d
on conflict do nothing;

-- ---------------------------------------------------------------------
-- ONGs, unidades e vínculos
-- ---------------------------------------------------------------------
insert into public.ong (id, nome, email_contato, telefone, descricao, site, causa) values
  ('00000000-0000-4000-8000-000000000201', 'Instituto Raízes', 'contato@raizes.org.br',
   '3133334444',
   'Apoio a famílias em vulnerabilidade com distribuição de alimentos, reforço escolar e oficinas de geração de renda.',
   'https://raizes.org.br', 'assistencia_social'),
  ('00000000-0000-4000-8000-000000000202', 'Patas Unidas', 'ola@patasunidas.org',
   '3135556666',
   'Resgate, castração e adoção responsável de cães e gatos na região metropolitana.',
   null, 'animais')
on conflict do nothing;

insert into public.unidade (id, ong_id, nome, logradouro, numero, bairro, cidade, uf, cep) values
  ('00000000-0000-4000-8000-000000000301', '00000000-0000-4000-8000-000000000201',
   'Sede Centro', 'Rua dos Guajajaras', '1200', 'Centro', 'Belo Horizonte', 'MG', '30180100'),
  ('00000000-0000-4000-8000-000000000302', '00000000-0000-4000-8000-000000000201',
   'Núcleo Barreiro', 'Av. Afonso Vaz de Melo', '640', 'Barreiro', 'Belo Horizonte', 'MG', '30640070'),
  ('00000000-0000-4000-8000-000000000303', '00000000-0000-4000-8000-000000000202',
   'Abrigo Contagem', 'Rua das Acácias', '85', 'Eldorado', 'Contagem', 'MG', '32315040')
on conflict do nothing;

insert into public.ong_membro (usuario_id, ong_id, unidade_id, papel) values
  ('00000000-0000-4000-8000-000000000002', '00000000-0000-4000-8000-000000000201', null, 'proprietario'),
  ('00000000-0000-4000-8000-000000000003', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000302', 'operador'),
  ('00000000-0000-4000-8000-000000000004', '00000000-0000-4000-8000-000000000202', null, 'proprietario')
on conflict do nothing;

-- ---------------------------------------------------------------------
-- Ações
-- ---------------------------------------------------------------------
insert into public.acao_social
  (id, ong_id, unidade_id, titulo, descricao, local_texto, inicio, fim, vagas, status, causa, criado_por)
values
  ('00000000-0000-4000-8000-000000000401', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000301', 'Distribuição de cestas básicas',
   'Montagem e entrega de cestas para 120 famílias cadastradas. Use roupa confortável e calçado fechado.',
   'Galpão nos fundos da sede', pg_temp.quando(3, '09:00'), pg_temp.quando(3, '12:00'), 15,
   'publicada', 'assistencia_social', '00000000-0000-4000-8000-000000000002'),
  ('00000000-0000-4000-8000-000000000402', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000302', 'Reforço escolar de matemática',
   'Acompanhamento de alunos do ensino fundamental com exercícios de frações e porcentagem.',
   null, pg_temp.quando(5, '14:00'), pg_temp.quando(5, '17:00'), 8,
   'publicada', 'educacao', '00000000-0000-4000-8000-000000000003'),
  ('00000000-0000-4000-8000-000000000403', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000301', 'Oficina de culinária (1 vaga)',
   'Preparo de marmitas com a cozinheira da casa. Apenas uma vaga: ideal para demonstrar a disputa pela última vaga.',
   'Cozinha comunitária', pg_temp.quando(2, '10:00'), pg_temp.quando(2, '12:00'), 1,
   'publicada', 'assistencia_social', '00000000-0000-4000-8000-000000000002'),
  ('00000000-0000-4000-8000-000000000404', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000301', 'Campanha do agasalho',
   'Triagem de roupas doadas. Ainda em planejamento.',
   null, pg_temp.quando(12, '09:00'), pg_temp.quando(12, '13:00'), 20,
   'rascunho', 'assistencia_social', '00000000-0000-4000-8000-000000000002'),
  ('00000000-0000-4000-8000-000000000405', '00000000-0000-4000-8000-000000000201',
   '00000000-0000-4000-8000-000000000301', 'Plantio de mudas no quarteirão',
   'Plantio de 40 mudas nativas nas calçadas do entorno da sede.',
   null, pg_temp.quando(-7, '08:00'), pg_temp.quando(-7, '11:00'), 10,
   'publicada', 'meio_ambiente', '00000000-0000-4000-8000-000000000002'),
  ('00000000-0000-4000-8000-000000000406', '00000000-0000-4000-8000-000000000202',
   '00000000-0000-4000-8000-000000000303', 'Feira de adoção',
   'Ajuda no cuidado dos animais e na conversa com as famílias interessadas.',
   'Praça do Eldorado', pg_temp.quando(4, '09:00'), pg_temp.quando(4, '13:00'), 6,
   'publicada', 'animais', '00000000-0000-4000-8000-000000000004')
on conflict do nothing;

insert into public.acao_habilidade (acao_id, habilidade_id, obrigatoria)
select a.acao_id, h.id, a.obrigatoria
  from (values
    ('00000000-0000-4000-8000-000000000401'::uuid, 'Logística e estoque', false),
    ('00000000-0000-4000-8000-000000000402'::uuid, 'Ensino e reforço escolar', true),
    ('00000000-0000-4000-8000-000000000403'::uuid, 'Cozinha e alimentação', false),
    ('00000000-0000-4000-8000-000000000406'::uuid, 'Cuidado com animais', false)
  ) as a(acao_id, nome, obrigatoria)
  join public.habilidade h on h.nome = a.nome
on conflict do nothing;

-- ---------------------------------------------------------------------
-- Inscrições, presença e histórico
-- ---------------------------------------------------------------------
insert into public.inscricao (id, acao_id, voluntario_id, status) values
  ('00000000-0000-4000-8000-000000000501', '00000000-0000-4000-8000-000000000401',
   '00000000-0000-4000-8000-000000000105', 'confirmada'),
  ('00000000-0000-4000-8000-000000000502', '00000000-0000-4000-8000-000000000405',
   '00000000-0000-4000-8000-000000000105', 'confirmada'),
  ('00000000-0000-4000-8000-000000000503', '00000000-0000-4000-8000-000000000405',
   '00000000-0000-4000-8000-000000000106', 'confirmada')
on conflict do nothing;

-- Ana esteve no plantio (3 horas); Bruno faltou.
insert into public.presenca (inscricao_id, check_in, check_out, registrado_por) values
  ('00000000-0000-4000-8000-000000000502', pg_temp.quando(-7, '08:00'), pg_temp.quando(-7, '11:00'),
   '00000000-0000-4000-8000-000000000002')
on conflict do nothing;

-- Só agora a ação passada é concluída: o trigger de inscrição não aceita
-- inscrever em ação concluída.
update public.acao_social set status = 'concluida'
 where id = '00000000-0000-4000-8000-000000000405';

insert into public.notificacao (usuario_id, acao_id, tipo, titulo, mensagem, lida) values
  ('00000000-0000-4000-8000-000000000005', '00000000-0000-4000-8000-000000000403', 'acao_criada',
   'Nova ação com a sua cara', 'Instituto Raízes publicou a ação "Oficina de culinária (1 vaga)".', false),
  ('00000000-0000-4000-8000-000000000002', '00000000-0000-4000-8000-000000000401', 'inscricao_confirmada',
   'Nova inscrição', 'Ana Clara Ribeiro se inscreveu em "Distribuição de cestas básicas".', false);

commit;
