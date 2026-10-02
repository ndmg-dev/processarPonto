import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    tarefa = asyncio.create_task(_tarefa_periodica_de_expurgo())
    yield
    tarefa.cancel()


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
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return _erro("ERRO", str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc: RequestValidationError):
    return _erro("ENTRADA_INVALIDA", "Dados de entrada inválidos.", 422)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, _exc: Exception):
    # Nenhum stack trace vai para o cliente.
    return _erro("ERRO_INTERNO", "Erro interno. Tente novamente.", 500)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return _erro("ARQUIVO_INVALIDO", "Apenas arquivos PDF são aceitos.")

    conteudo = await file.read()
    if len(conteudo) > MAX_UPLOAD_BYTES:
        return _erro("ARQUIVO_MUITO_GRANDE", "O arquivo excede o limite de 10 MB.")
    if not conteudo.startswith(b"%PDF-"):
        return _erro("ARQUIVO_INVALIDO", "O arquivo não é um PDF válido.")

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
            return _erro("ARQUIVO_INVALIDO", f"O PDF excede o limite de {MAX_PAGINAS} páginas.")

        employees = await asyncio.wait_for(
            asyncio.to_thread(parse_pdf_pages, pages_text, pages_words), timeout=PARSING_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        return _erro("TEMPO_ESGOTADO", "O processamento do PDF excedeu o tempo limite.", 422)
    except LayoutError:
        return _erro("LAYOUT_NAO_SUPORTADO", "O layout deste PDF não é reconhecido.", 422)
    finally:
        # O PDF original não precisa ficar em disco depois de extraído —
        # só os dados já estruturados (retenção mínima).
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)

    result = {
        "upload_id": upload_id,
        "file_name": file.filename,
        "total_employees": len(employees),
        "employees": employees,
    }
    storage.save(upload_id, storage.UploadMeta(upload_id=upload_id, criado_em=time.time()), result)

    return result


def _extrair_paginas(path: str):
    return extract_pages_text(path), extract_pages_words(path)


@app.get("/api/uploads/{upload_id}")
async def get_upload_result(upload_id: str):
    resultado = storage.load_result(upload_id)
    if resultado is None:
        return _erro("PROCESSAMENTO_NAO_ENCONTRADO", "Processamento não encontrado.", 404)
    return resultado


@app.post("/api/uploads/{upload_id}/report")
async def generate_report(upload_id: str):
    resultado = storage.load_result(upload_id)
    if resultado is None:
        return _erro("PROCESSAMENTO_NAO_ENCONTRADO", "Processamento não encontrado.", 404)

    report_path = storage.report_target_path(upload_id)
    await asyncio.to_thread(generate_pdf_report, resultado, report_path)

    return {"report_url": f"/api/reports/relatorio_{upload_id}.pdf"}


@app.get("/api/reports/{file_name}")
def download_report(file_name: str):
    report_path = os.path.join(storage.REPORT_DIR, file_name)
    if not os.path.exists(report_path):
        return _erro("RELATORIO_NAO_ENCONTRADO", "Relatório não encontrado.", 404)
    return FileResponse(report_path, media_type="application/pdf", filename=file_name)
