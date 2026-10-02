-- Fase 2 — modelo de dados multi-tenant (ver reestruturacao-processar-ponto.md §7.2).
-- organizacao_id fica desnormalizado nas tabelas filhas de propósito: assim as
-- policies de RLS não precisam de join, e o tenant fica explícito em cada linha.

create extension if not exists pgcrypto;

create type papel as enum ('admin', 'analista', 'leitura');
create type status_lote as enum ('RECEBIDO','PROCESSANDO','OK','COM_PENDENCIAS','ERRO_LEITURA','ERRO_LAYOUT');
create type classificacao_dia as enum (
  'TRABALHADO','DOMINGO','SABADO','FERIADO','ATESTADO_INTEGRAL','ATESTADO_PARCIAL',
  'FALTA_INTEGRAL','FALTA_PARCIAL','MARCACAO_IMPAR');

create table organizacoes (
  id uuid primary key default gen_random_uuid(),
  nome text not null
);

create table membros (
  organizacao_id uuid not null references organizacoes(id),
  user_id uuid not null references auth.users(id),
  papel papel not null,
  acesso_total boolean not null default false,   -- false = só carteira
  primary key (organizacao_id, user_id)
);

create table empresas (
  id uuid primary key default gen_random_uuid(),
  organizacao_id uuid not null references organizacoes(id),
  cnpj char(14) not null,
  razao_social text not null,
  unique (organizacao_id, cnpj)
);

create table carteira (
  organizacao_id uuid not null,
  user_id uuid not null,
  empresa_id uuid not null references empresas(id),
  primary key (user_id, empresa_id)
);

create table lotes (
  id uuid primary key default gen_random_uuid(),
  organizacao_id uuid not null references organizacoes(id),
  empresa_id uuid not null references empresas(id),
  competencia date not null,                     -- 1º dia do mês
  periodo_inicio date not null,
  periodo_fim date not null,
  emissao date,
  layout text not null,
  arquivo_sha256 char(64) not null,
  arquivo_path text,                             -- null após expurgo do PDF
  nome_exibicao text not null,                   -- sanitizado
  versao int not null default 1,
  status status_lote not null default 'RECEBIDO',
  criado_por uuid not null references auth.users(id),
  criado_em timestamptz not null default now(),
  expurgar_em timestamptz not null,
  unique (empresa_id, competencia, versao)
);

create table colaboradores (
  id uuid primary key default gen_random_uuid(),
  organizacao_id uuid not null,
  empresa_id uuid not null references empresas(id),
  matricula text not null,
  nome text not null,
  cpf_enc bytea,                                 -- CPF cifrado (pgcrypto/Vault); decifrado só na API
  cpf_hash char(64),                             -- HMAC-SHA256(cpf, pepper) para busca exata
  cpf_mascarado text,                            -- '***.456.789-**' para exibição
  dominio_codigo_empregado int,                  -- vínculo com o cadastro do Domínio
  vinculo_status text not null default 'PENDENTE', -- PENDENTE | AUTOMATICO | CONFIRMADO | DIVERGENTE
  cargo text,
  admissao date,
  setor_codigo text,
  setor_descricao text,
  unique (empresa_id, matricula)
);

create table espelhos (
  id uuid primary key default gen_random_uuid(),
  organizacao_id uuid not null,
  lote_id uuid not null references lotes(id) on delete cascade,
  colaborador_id uuid not null references colaboradores(id),
  pagina int not null,
  horario text not null,
  status status_lote not null,
  -- resumo (minutos, com sinal)
  horas_normais int, dsr_normais int, total_semanal int, saldo_banco int,
  adc_noturno int, tot_descontado int,
  extra_50 int, extra_70 int, extra_100 int,
  h_trab_pagos int, dsr_pagos int, dsr_desc int, atrasos_desc int,
  faltas_pagos int, faltas_desc int, saidas_antecipadas_desc int,
  unique (lote_id, colaborador_id)
);

create table espelho_dias (
  organizacao_id uuid not null,
  espelho_id uuid not null references espelhos(id) on delete cascade,
  data date not null,
  marcacoes jsonb not null default '{}',         -- {slot: "HH:MM"}
  ocorrencias jsonb not null default '{}',       -- {slot: "FALTA"|"MEDIC"|...}
  horas_trab int not null default 0,
  horas_desc int not null default 0,
  quadro text[] not null default '{}',
  observacao text,
  classificacao classificacao_dia not null,
  primary key (espelho_id, data)
);

create table pendencias (
  id bigint generated always as identity primary key,
  organizacao_id uuid not null,
  espelho_id uuid not null references espelhos(id) on delete cascade,
  codigo text not null,                          -- CK_* / AL_*
  bloqueante boolean not null,
  data date,
  detalhe jsonb not null default '{}',
  resolvida_por uuid, resolvida_em timestamptz
);

create table auditoria (
  id bigint generated always as identity primary key,
  organizacao_id uuid not null,
  user_id uuid not null,
  acao text not null,                            -- UPLOAD, VISUALIZAR, EXPORTAR, EXCLUIR
  recurso text not null,
  recurso_id uuid,
  em timestamptz not null default now()
  -- sem nomes, sem marcações: só IDs
);

create index on lotes (organizacao_id, empresa_id, competencia);
create index on espelhos (lote_id);
create index on pendencias (espelho_id) where resolvida_em is null;
