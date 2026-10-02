"""Armazenamento efêmero do upload processado — este sistema não guarda
colaborador nem dia de ponto em banco (decisão de produto: processa, gera
relatório, exporta, esquece). O resultado fica em disco só pelo tempo da
"sessão" (EXPURGO_TTL_SECONDS) e é apagado por um job periódico ou on
-demand (DELETE /api/uploads/{id})."""

import json
import os
import time
from dataclasses import asdict, dataclass

UPLOAD_DIR = "app/storage/uploads"
REPORT_DIR = "app/storage/reports"
EXPURGO_TTL_SECONDS = int(os.environ.get("EXPURGO_TTL_SECONDS", str(2 * 60 * 60)))  # 2h por padrão

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


@dataclass
class UploadMeta:
    upload_id: str
    organizacao_id: str
    empresa_id: str
    criado_por: str
    criado_em: float


def _meta_path(upload_id: str) -> str:
    return os.path.join(UPLOAD_DIR, f"{upload_id}.meta.json")


def _result_path(upload_id: str) -> str:
    return os.path.join(UPLOAD_DIR, f"{upload_id}.json")


def _report_path(upload_id: str) -> str:
    return os.path.join(REPORT_DIR, f"relatorio_{upload_id}.pdf")


def save(upload_id: str, meta: UploadMeta, result: dict) -> None:
    with open(_meta_path(upload_id), "w", encoding="utf-8") as f:
        json.dump(asdict(meta), f, ensure_ascii=False)
    with open(_result_path(upload_id), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def load_meta(upload_id: str) -> UploadMeta | None:
    path = _meta_path(upload_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return UploadMeta(**json.load(f))


def load_result(upload_id: str) -> dict | None:
    path = _result_path(upload_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def report_path_if_exists(upload_id: str) -> str | None:
    path = _report_path(upload_id)
    return path if os.path.exists(path) else None


def report_target_path(upload_id: str) -> str:
    return _report_path(upload_id)


def purge(upload_id: str) -> None:
    for path in (_meta_path(upload_id), _result_path(upload_id), _report_path(upload_id)):
        if os.path.exists(path):
            os.remove(path)


def purge_expirados() -> int:
    """Varre os uploads e apaga os que passaram do TTL. Chamado por uma
    tarefa periódica em background (ver main.py)."""
    agora = time.time()
    apagados = 0
    if not os.path.isdir(UPLOAD_DIR):
        return 0
    for nome in os.listdir(UPLOAD_DIR):
        if not nome.endswith(".meta.json"):
            continue
        upload_id = nome[: -len(".meta.json")]
        meta = load_meta(upload_id)
        if meta is None:
            continue
        if agora - meta.criado_em > EXPURGO_TTL_SECONDS:
            purge(upload_id)
            apagados += 1
    return apagados
