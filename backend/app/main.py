import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import ApiError, AuthUser, get_current_user, require_empresa_acesso
from app.auditoria import registrar
from app import db
from app import storage
from app.services.pdf_reader import extract_pages_text, extract_pages_words
from app.services.parser import parse_pdf_pages, LayoutError
from app.services.report_generator import generate_pdf_report

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB, §5.1
MAX_PAGINAS = 300
PARSING_TIMEOUT_SECONDS = 60
LIMPEZA_INTERVALO_SEGUNDOS = 15 * 60


async def _tarefa_periodica_de_expurgo():
    while True:
        await asyncio.sleep(LIMPEZA_INTERVALO_SEGUNDOS)
        try:
            storage.purge_expirados()
        except Exception:
            # Falha na limpeza não pode derrubar a API — tenta de novo no
            # próximo ciclo.
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    tarefa = asyncio.create_task(_tarefa_periodica_de_expurgo())
    yield
    tarefa.cancel()
    await db.close_pool()


app = FastAPI(title="Processar Ponto", lifespan=lifespan)

# CORS — restrito às origens de verdade do sistema. CORS_ORIGINS permite
# sobrescrever por ambiente (ex.: localhost na dev), sem voltar a liberar "*"
# com allow_credentials=True (essa combinação é proibida pelo browser e, se
# fosse aceita, deixaria qualquer site ler as respostas autenticadas).
_default_origins = "https://processarponto.mendoncagalvao.com.br"
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _erro(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request, exc: StarletteHTTPException):
    # ApiError já chega aqui com detail={"code","message"}; HTTPException
    # "crua" (ex.: 404 de rota) vira o mesmo formato, nunca stack trace.
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return _erro("ERRO", str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    return _erro("ENTRADA_INVALIDA", "Dados de entrada inválidos.", 422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, _exc: Exception):
    # Nenhum stack trace vai para o cliente (§9).
    return _erro("ERRO_INTERNO", "Erro interno. Tente novamente.", 500)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/uploads")
async def upload_file(
    file: UploadFile = File(...),
    empresa_id: str = Form(...),
    user: AuthUser = Depends(get_current_user),
):
    organizacao_id = await require_empresa_acesso(empresa_id, user)

    if not file.filename.endswith(".pdf"):
        raise ApiError(400, "ARQUIVO_INVALIDO", "Apenas arquivos PDF são aceitos.")

    conteudo = await file.read()
    if len(conteudo) > MAX_UPLOAD_BYTES:
        raise ApiError(400, "ARQUIVO_MUITO_GRANDE", "O arquivo excede o limite de 10 MB.")
    if not conteudo.startswith(b"%PDF-"):
        raise ApiError(400, "ARQUIVO_INVALIDO", "O arquivo não é um PDF válido.")

    upload_id = str(uuid.uuid4())
    # Nome salvo por UUID — o nome original só é usado para exibição,
    # nunca para localizar o arquivo em disco (§5.1).
    tmp_pdf_path = os.path.join(storage.UPLOAD_DIR, f"{upload_id}.pdf")
    with open(tmp_pdf_path, "wb") as buffer:
        buffer.write(conteudo)

    try:
        pages_text, pages_words = await asyncio.wait_for(
            asyncio.to_thread(_extrair_paginas, tmp_pdf_path), timeout=PARSING_TIMEOUT_SECONDS
        )
        if len(pages_text) > MAX_PAGINAS:
            raise ApiError(400, "ARQUIVO_INVALIDO", f"O PDF excede o limite de {MAX_PAGINAS} páginas.")

        employees = await asyncio.wait_for(
            asyncio.to_thread(parse_pdf_pages, pages_text, pages_words), timeout=PARSING_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        raise ApiError(422, "TEMPO_ESGOTADO", "O processamento do PDF excedeu o tempo limite.")
    except LayoutError:
        raise ApiError(422, "LAYOUT_NAO_SUPORTADO", "O layout deste PDF não é reconhecido.")
    finally:
        # O PDF original não precisa ficar em disco depois de extraído —
        # só os dados já estruturados (retenção mínima, §8.3).
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)

    result = {
        "upload_id": upload_id,
        "file_name": file.filename,
        "total_employees": len(employees),
        "employees": employees,
    }
    meta = storage.UploadMeta(
        upload_id=upload_id,
        organizacao_id=organizacao_id,
        empresa_id=empresa_id,
        criado_por=user.user_id,
        criado_em=time.time(),
    )
    storage.save(upload_id, meta, result)
    await registrar(user, organizacao_id, "UPLOAD", "upload", upload_id)

    return result


def _extrair_paginas(path: str):
    return extract_pages_text(path), extract_pages_words(path)


async def _carregar_com_permissao(upload_id: str, user: AuthUser) -> tuple[storage.UploadMeta, dict]:
    meta = storage.load_meta(upload_id)
    resultado = storage.load_result(upload_id)
    if meta is None or resultado is None:
        raise ApiError(404, "PROCESSAMENTO_NAO_ENCONTRADO", "Processamento não encontrado.")

    # Confere a posse por empresa/carteira de novo (o upload pode ter sido
    # feito por outro usuário da mesma organização) — nunca confia só no
    # fato de ter adivinhado o upload_id (anti-IDOR, §11.2.8). 404, não 403.
    organizacao_id_confirmado = await require_empresa_acesso(meta.empresa_id, user)
    if organizacao_id_confirmado != meta.organizacao_id:
        raise ApiError(404, "PROCESSAMENTO_NAO_ENCONTRADO", "Processamento não encontrado.")

    return meta, resultado


@app.get("/api/uploads/{upload_id}")
async def get_upload_result(upload_id: str, user: AuthUser = Depends(get_current_user)):
    meta, resultado = await _carregar_com_permissao(upload_id, user)
    await registrar(user, meta.organizacao_id, "VISUALIZAR", "upload", upload_id)
    return resultado


@app.post("/api/uploads/{upload_id}/export")
async def export_report(upload_id: str, user: AuthUser = Depends(get_current_user)):
    meta, resultado = await _carregar_com_permissao(upload_id, user)

    report_path = storage.report_target_path(upload_id)
    await asyncio.to_thread(generate_pdf_report, resultado, report_path)
    await registrar(user, meta.organizacao_id, "EXPORTAR", "upload", upload_id)

    return {"report_url": f"/api/uploads/{upload_id}/export"}


@app.get("/api/uploads/{upload_id}/export")
async def download_report(upload_id: str, user: AuthUser = Depends(get_current_user)):
    await _carregar_com_permissao(upload_id, user)
    report_path = storage.report_path_if_exists(upload_id)
    if report_path is None:
        raise ApiError(404, "RELATORIO_NAO_ENCONTRADO", "Gere o relatório antes de baixar.")
    return FileResponse(report_path, media_type="application/pdf", filename=f"relatorio_{upload_id}.pdf")


@app.delete("/api/uploads/{upload_id}")
async def delete_upload(upload_id: str, user: AuthUser = Depends(get_current_user)):
    meta, _resultado = await _carregar_com_permissao(upload_id, user)
    storage.purge(upload_id)
    await registrar(user, meta.organizacao_id, "EXCLUIR", "upload", upload_id)
    return {"status": "ok"}
