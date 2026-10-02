-- Aplicado por último, só no ambiente de teste: dá ao papel "authenticated"
-- o acesso que a RLS depois restringe linha a linha. Sem isso a RLS nunca
-- chega a ser exercitada (o grant de tabela falha primeiro).

grant usage on schema public, auth to authenticated;
grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;
