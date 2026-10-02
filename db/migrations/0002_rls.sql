-- Fase 2 — RLS (ver reestruturacao-processar-ponto.md §7.3).
-- Defesa em profundidade: a API também filtra por organizacao_id/empresa_id a
-- partir do JWT, sem depender só da RLS (ver nota no final do arquivo).

create or replace function app_pode_ver_empresa(p_org uuid, p_empresa uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from membros m
    where m.user_id = auth.uid() and m.organizacao_id = p_org
      and (m.acesso_total or exists (
        select 1 from carteira c where c.user_id = m.user_id and c.empresa_id = p_empresa))
  );
$$;

create or replace function app_papel(p_org uuid)
returns papel language sql stable security definer set search_path = public as $$
  select papel from membros where user_id = auth.uid() and organizacao_id = p_org;
$$;

-- lotes ------------------------------------------------------------------

alter table lotes enable row level security;
alter table lotes force row level security;

create policy lotes_select on lotes for select
  using (app_pode_ver_empresa(organizacao_id, empresa_id));
create policy lotes_insert on lotes for insert
  with check (app_pode_ver_empresa(organizacao_id, empresa_id)
              and app_papel(organizacao_id) in ('admin','analista')
              and criado_por = auth.uid());
create policy lotes_delete on lotes for delete
  using (app_papel(organizacao_id) = 'admin');

-- empresas -----------------------------------------------------------------

alter table empresas enable row level security;
alter table empresas force row level security;

create policy empresas_select on empresas for select
  using (app_pode_ver_empresa(organizacao_id, id));
create policy empresas_insert on empresas for insert
  with check (app_papel(organizacao_id) = 'admin');
create policy empresas_update on empresas for update
  using (app_papel(organizacao_id) = 'admin');

-- colaboradores --------------------------------------------------------------

alter table colaboradores enable row level security;
alter table colaboradores force row level security;

create policy colaboradores_select on colaboradores for select
  using (app_pode_ver_empresa(organizacao_id, empresa_id));

-- escrita de colaboradores: somente pelo worker (service role), nunca pelo
-- cliente — o cadastro vem do parsing + cruzamento com o Domínio.
revoke insert, update on colaboradores from authenticated;

-- espelhos / espelho_dias / pendencias: select via lote visível -------------

create policy espelhos_select on espelhos for select using (
  exists (select 1 from lotes l where l.id = lote_id
          and app_pode_ver_empresa(l.organizacao_id, l.empresa_id)));

alter table espelhos enable row level security;
alter table espelhos force row level security;

create policy espelho_dias_select on espelho_dias for select using (
  exists (
    select 1 from espelhos e join lotes l on l.id = e.lote_id
    where e.id = espelho_id and app_pode_ver_empresa(l.organizacao_id, l.empresa_id)));

alter table espelho_dias enable row level security;
alter table espelho_dias force row level security;

create policy pendencias_select on pendencias for select using (
  exists (
    select 1 from espelhos e join lotes l on l.id = e.lote_id
    where e.id = espelho_id and app_pode_ver_empresa(l.organizacao_id, l.empresa_id)));

create policy pendencias_update on pendencias for update using (
  exists (
    select 1 from espelhos e join lotes l on l.id = e.lote_id
    where e.id = espelho_id and app_pode_ver_empresa(l.organizacao_id, l.empresa_id)
      and app_papel(l.organizacao_id) in ('admin','analista')));

alter table pendencias enable row level security;
alter table pendencias force row level security;

-- escrita de parsing: somente pelo worker (service role), nunca pelo cliente
revoke insert, update on espelhos, espelho_dias, pendencias from authenticated;

-- auditoria ------------------------------------------------------------------

alter table auditoria enable row level security;
alter table auditoria force row level security;

create policy auditoria_select on auditoria for select
  using (app_papel(organizacao_id) = 'admin');

-- a auditoria é escrita pela própria API (não pelo cliente diretamente);
-- grant explícito evita depender do papel "authenticated" ter insert geral.
revoke insert on auditoria from authenticated;
