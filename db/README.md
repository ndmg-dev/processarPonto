# Modelo de dados (Fase 2)

`migrations/` tem o DDL e a RLS exatamente como especificados em
`reestruturacao-processar-ponto.md` §7. Em produção (Supabase), aplique os
dois arquivos na ordem, pelo SQL editor ou pela CLI do Supabase — o schema
`auth` e `auth.uid()` já existem lá.

## Rodando os testes de RLS localmente

Fora do Supabase, `auth.users`/`auth.uid()` não existem, então os testes
sobem um Postgres comum e aplicam um stub (`tests/fixtures/auth_stub.sql`)
antes das migrations de verdade:

```bash
export TEST_DB_PASSWORD=escolha-uma-senha-qualquer-local
docker compose --profile test up -d db
pip install -r db/requirements-test.txt
DATABASE_URL_ADMIN="postgresql://postgres:${TEST_DB_PASSWORD}@localhost:55432/postgres" \
  pytest db/tests
```

Os testes cobrem os três casos obrigatórios do §11.2.7:

1. usuário de outra organização recebe 0 linhas em todas as tabelas;
2. analista fora da carteira não vê a empresa;
3. papel `leitura` não consegue inserir lote.

> Não executado neste PR por falta de Docker com acesso ao daemon no
> ambiente onde este código foi escrito. Rodar localmente antes do merge.
