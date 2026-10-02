"""Casos obrigatórios de RLS — reestruturacao-processar-ponto.md §11.2.7.

1. usuário de outra organização recebe 0 linhas em todas as tabelas;
2. analista fora da carteira não vê a empresa;
3. papel "leitura" não consegue inserir lote.
"""

import psycopg2
import pytest


def test_outra_organizacao_nao_ve_nada(cenario, as_user):
    conn = as_user(cenario["user_b"])
    with conn.cursor() as cur:
        cur.execute("select count(*) from lotes")
        assert cur.fetchone()[0] == 0
        cur.execute("select count(*) from empresas")
        assert cur.fetchone()[0] == 0


def test_analista_fora_da_carteira_nao_ve_empresa(cenario, as_user):
    conn = as_user(cenario["analista_a"])
    with conn.cursor() as cur:
        cur.execute("select id from empresas order by razao_social")
        vistas = {row[0] for row in cur.fetchall()}
        assert cenario["empresa_a1"] in vistas
        assert cenario["empresa_a2"] not in vistas


def test_papel_leitura_nao_insere_lote(cenario, as_user):
    conn = as_user(cenario["leitura_a"])
    with conn.cursor() as cur, pytest.raises(psycopg2.errors.InsufficientPrivilege):
        cur.execute(
            "insert into lotes (organizacao_id, empresa_id, competencia, periodo_inicio, "
            "periodo_fim, layout, arquivo_sha256, nome_exibicao, criado_por, expurgar_em) "
            "values (%s,%s,'2026-02-01','2026-02-01','2026-02-28','acesso-v4.5', repeat('b',64), "
            "'outro.pdf', %s, now() + interval '30 days')",
            (cenario["org_a"], cenario["empresa_a1"], cenario["leitura_a"]),
        )
    conn.rollback()
