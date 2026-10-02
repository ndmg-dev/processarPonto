"""Acesso ao Postgres — usado só para o que é persistente de verdade neste
sistema: organizacoes/membros/empresas/carteira (quem pode logar e quais
empresas atende) e auditoria (quem viu/exportou/excluiu o quê, sem PII).

O upload/processamento em si continua efêmero (ver app/storage.py) — este
sistema não guarda colaborador nem dia de ponto em banco nenhum."""

import os
from contextlib import asynccontextmanager

import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("defina DATABASE_URL (Postgres do Supabase) para a API subir")
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def db_conn(jwt_claims_json: str | None = None):
    """Abre uma conexão e, se houver um JWT autenticado, replica o que o
    PostgREST faz antes de cada query: publica os claims na GUC que
    auth.uid() lê e assume o papel "authenticated", para a RLS valer mesmo
    conectando direto (defesa em profundidade, ver
    reestruturacao-processar-ponto.md §7.3). Use para toda leitura que deve
    respeitar a carteira do usuário."""
    if _pool is None:
        raise RuntimeError("pool de conexões não inicializado — init_pool() não foi chamado")
    async with _pool.acquire() as conn:
        async with conn.transaction():
            if jwt_claims_json is not None:
                await conn.execute("select set_config('request.jwt.claims', $1, true)", jwt_claims_json)
                await conn.execute("set local role authenticated")
            yield conn


@asynccontextmanager
async def db_conn_admin():
    """Conexão sem downgrade de papel — só para escritas que a própria API
    controla e que a RLS deliberadamente revogou de "authenticated" (ex.:
    auditoria, ver migrations 0002_rls.sql). Nunca use isto para atender uma
    leitura disparada por um usuário: aqui não há RLS nenhuma te protegendo
    de vazar dado de outro tenant."""
    if _pool is None:
        raise RuntimeError("pool de conexões não inicializado — init_pool() não foi chamado")
    async with _pool.acquire() as conn:
        async with conn.transaction():
            yield conn
