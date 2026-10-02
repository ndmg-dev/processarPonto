-- Stub do schema "auth" do Supabase, só para rodar as migrations e os
-- testes de RLS num Postgres comum (local/CI). Em produção o Supabase já
-- fornece auth.users e auth.uid() de verdade — este arquivo nunca é
-- aplicado lá.

create schema if not exists auth;

create table if not exists auth.users (
  id uuid primary key default gen_random_uuid()
);

create or replace function auth.uid() returns uuid
language sql stable as $$
  select nullif(current_setting('app.current_user_id', true), '')::uuid
$$;

-- Papel usado pela API/pelos testes, sem BYPASSRLS — é o que faz a RLS
-- valer de fato (o owner das tabelas, por padrão, ignora as policies).
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end
$$;
