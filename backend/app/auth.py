"""Autenticação (JWT do Supabase Auth) e autorização por empresa/carteira
(reestruturacao-processar-ponto.md §9: "O org_id vem do token e nunca do
body"). Como este projeto ainda não usa custom claims no Supabase, o
organizacao_id não vem embutido no JWT — é resolvido a cada request, a
partir do `sub` (user_id) já validado, contra a tabela `membros`. Isso
preserva a garantia ("nunca do body"): o client nunca escolhe a org, só o
servidor, consultando o que está de fato associado àquele usuário."""

import json
import os
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import db_conn

bearer_scheme = HTTPBearer(auto_error=False)


class ApiError(HTTPException):
    """Erro com o formato {"code", "message"} exigido pela API (§9) —
    nenhum stack trace vai para o cliente."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


@dataclass
class AuthUser:
    user_id: str
    email: str | None
    claims_json: str


def _get_jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        raise RuntimeError("defina SUPABASE_JWT_SECRET para validar os tokens do Supabase Auth")
    return secret


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> AuthUser:
    if credentials is None:
        raise ApiError(401, "NAO_AUTENTICADO", "Token de acesso ausente.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_jwt_secret(),
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise ApiError(401, "TOKEN_INVALIDO", "Token de acesso inválido ou expirado.")

    user_id = payload.get("sub")
    if not user_id:
        raise ApiError(401, "TOKEN_INVALIDO", "Token sem identificação de usuário.")

    # O "claims" publicado via set_config é só o que auth.uid() precisa —
    # nunca republicamos o JWT inteiro (ele pode ter outros dados do provedor).
    import json
    claims_json = json.dumps({"sub": user_id, "role": "authenticated"})

    return AuthUser(user_id=user_id, email=payload.get("email"), claims_json=claims_json)


async def require_empresa_acesso(empresa_id: str, user: AuthUser) -> str:
    """Confirma que o usuário autenticado pode operar nessa empresa (membro
    da organização dona dela, com acesso_total OU a empresa na carteira) e
    devolve o organizacao_id — resolvido aqui, nunca aceito do client."""
    async with db_conn(user.claims_json) as conn:
        row = await conn.fetchrow(
            """
            select e.organizacao_id
            from empresas e
            join membros m on m.organizacao_id = e.organizacao_id
            where e.id = $1::uuid
              and m.user_id = $2::uuid
              and (m.acesso_total or exists (
                    select 1 from carteira c
                    where c.user_id = m.user_id and c.empresa_id = e.id))
            """,
            empresa_id,
            user.user_id,
        )
    if row is None:
        # 404, não 403: não confirma pra fora se a empresa existe (anti-IDOR, §11.2.8).
        raise ApiError(404, "EMPRESA_NAO_ENCONTRADA", "Empresa não encontrada.")
    return str(row["organizacao_id"])
