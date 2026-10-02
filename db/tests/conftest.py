"""Infra de teste para a RLS (§11.2.7 da especificação).

Requer um Postgres vazio acessível por DATABASE_URL_ADMIN (superuser) —
ver db/README.md para subir um com docker compose. Cada teste roda num
savepoint próprio e é desfeito no final, então a base pode ser reutilizada
entre execuções.
"""

import os
import uuid
from pathlib import Path

import psycopg2
import pytest

DB_DIR = Path(__file__).resolve().parent.parent
ADMIN_DSN = os.environ.get("DATABASE_URL_ADMIN")
if not ADMIN_DSN:
    raise RuntimeError(
        "defina DATABASE_URL_ADMIN (ex.: postgresql://postgres:<TEST_DB_PASSWORD>@localhost:55432/postgres) "
        "— ver db/README.md"
    )


def _run_sql_file(cur, path: Path):
    cur.execute(path.read_text())


@pytest.fixture(scope="session")
def admin_conn():
    conn = psycopg2.connect(ADMIN_DSN)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("select 1 from pg_namespace where nspname = 'auth'")
        already_applied = cur.fetchone() is not None
        if not already_applied:
            _run_sql_file(cur, DB_DIR / "tests" / "fixtures" / "auth_stub.sql")
            _run_sql_file(cur, DB_DIR / "migrations" / "0001_initial_schema.sql")
            _run_sql_file(cur, DB_DIR / "migrations" / "0002_rls.sql")
            _run_sql_file(cur, DB_DIR / "tests" / "fixtures" / "test_grants.sql")
    yield conn
    conn.close()


@pytest.fixture
def cenario(admin_conn):
    """Cria duas organizações, cada uma com uma empresa e um membro, mais
    uma segunda empresa na org A fora da carteira do analista — o suficiente
    para os três casos obrigatórios do §11.2.7."""
    with admin_conn.cursor() as cur:
        org_a, org_b = uuid.uuid4(), uuid.uuid4()
        admin_a, analista_a, leitura_a, user_b = (
            uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        )
        empresa_a1, empresa_a2, empresa_b = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        cur.execute("insert into auth.users (id) values (%s),(%s),(%s),(%s)",
                    (admin_a, analista_a, leitura_a, user_b))
        cur.execute("insert into organizacoes (id, nome) values (%s,'Org A'),(%s,'Org B')",
                    (org_a, org_b))
        cur.execute(
            "insert into membros (organizacao_id, user_id, papel, acesso_total) values "
            "(%s,%s,'admin', true), (%s,%s,'analista', false), (%s,%s,'leitura', false),"
            "(%s,%s,'admin', true)",
            (org_a, admin_a, org_a, analista_a, org_a, leitura_a, org_b, user_b),
        )
        cur.execute(
            "insert into empresas (id, organizacao_id, cnpj, razao_social) values "
            "(%s,%s,'11111111000111','Empresa A1'), (%s,%s,'22222222000122','Empresa A2'), "
            "(%s,%s,'33333333000133','Empresa B')",
            (empresa_a1, org_a, empresa_a2, org_a, empresa_b, org_b),
        )
        # analista_a só enxerga a empresa_a1 (carteira restrita)
        cur.execute(
            "insert into carteira (organizacao_id, user_id, empresa_id) values (%s,%s,%s)",
            (org_a, analista_a, empresa_a1),
        )
        cur.execute(
            "insert into lotes (organizacao_id, empresa_id, competencia, periodo_inicio, "
            "periodo_fim, layout, arquivo_sha256, nome_exibicao, criado_por, expurgar_em) "
            "values (%s,%s,'2026-02-01','2026-02-01','2026-02-28','acesso-v4.5', repeat('a',64), "
            "'teste.pdf', %s, now() + interval '30 days')",
            (org_a, empresa_a1, admin_a),
        )
    admin_a_conn = None
    return {
        "org_a": org_a, "org_b": org_b,
        "admin_a": admin_a, "analista_a": analista_a, "leitura_a": leitura_a, "user_b": user_b,
        "empresa_a1": empresa_a1, "empresa_a2": empresa_a2, "empresa_b": empresa_b,
    }


@pytest.fixture
def as_user():
    """Retorna uma função que abre uma conexão autenticada como um usuário
    específico (papel "authenticated", auth.uid() == user_id)."""
    conexoes = []

    def _conectar(user_id):
        conn = psycopg2.connect(ADMIN_DSN)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("set role authenticated")
            cur.execute("select set_config('app.current_user_id', %s, false)", (str(user_id),))
        conexoes.append(conn)
        return conn

    yield _conectar
    for c in conexoes:
        c.close()
