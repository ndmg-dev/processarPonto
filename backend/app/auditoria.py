"""Registro de auditoria (reestruturacao-processar-ponto.md §8.2/§9) — só
IDs, nunca nomes, CPF, marcações ou conteúdo do PDF."""

from app.auth import AuthUser
from app.db import db_conn_admin


async def registrar(user: AuthUser, organizacao_id: str, acao: str, recurso: str, recurso_id: str) -> None:
    # auditoria revoga insert de "authenticated" de propósito (0002_rls.sql)
    # — só a própria API escreve aqui, nunca o client.
    async with db_conn_admin() as conn:
        await conn.execute(
            """
            insert into auditoria (organizacao_id, user_id, acao, recurso, recurso_id)
            values ($1::uuid, $2::uuid, $3, $4, $5::uuid)
            """,
            organizacao_id,
            user.user_id,
            acao,
            recurso,
            recurso_id,
        )
