"""Layout "Cartão de Ponto" (Control iD) — família de layout completamente
diferente da "ESPELHO DE PONTO ELETRÔNICO" (parser.py/parser_rep.py): cada
página já traz, por dia, colunas PRÉ-CALCULADAS pelo próprio sistema de ponto
(TOTAL NORMAIS, TOTAL NOTURNO, DIA FALTA, FALTA E ATRASO, ABONO, EXTRA 50%,
EXTRA 100% e, às vezes, EXTRA 0%) em vez de só os horários batidos — então
aqui não recalculamos horas trabalhadas a partir das marcações, só lemos o
que o próprio arquivo já totalizou por dia.

Cabeçalho do colaborador (NOME DO FUNCIONÁRIO:, CPF DO FUNCIONÁRIO: etc.) e
o período (DE dd/mm/yyyy ATÉ dd/mm/yyyy) vêm cada um em uma única linha de
texto "Rótulo: Valor" — diferente das outras duas variantes, aqui dá pra usar
extract_labeled_field() sem gambiarra de linha.

Ocorrências de dia inteiro ou parcial (Folga, Folga Premium, Férias, Falta,
Declaração Médica, Abonar ausência no período, FERIADO) aparecem como texto
solto nas colunas de horário (PREVISTO/ENT.1/SAÍ.1/ENT.2/SAÍ.2) em vez de
código de 3-4 letras — por isso a classificação aqui é por palavra-chave no
texto da linha, não por contagem de marcações.
"""

import re
import uuid

from app.models.schemas import PointStatus
from app.services.parser import (
    TIME_RE,
    LayoutError,
    _xc,
    _yc,
    clean_text,
    extract_labeled_field,
    minutes_to_time,
    to_minutes,
)

FULL_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PERIOD_RE = re.compile(r"DE\s+(\d{2}/\d{2}/\d{4})\s+AT[ÉE]\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
PAREN_TAG_RE = re.compile(r"^\([IPMC]\)$")

HEADER_COL_NAMES = {
    "NORMAIS": "total_normais",
    "NOTURNO": "total_noturno",
    "FALTA": "dia_falta",
    "ATRASO": "falta_atraso",
    "ABONO": "abono",
    "0%": "extra_0",
    "50%": "extra_50",
    "100%": "extra_100",
}


def is_cartao_ponto_layout(words: list[tuple]) -> bool:
    return any(w[4] == "PREVISTO" for w in words)


def _find_header_yc(words: list[tuple]) -> float:
    previsto = [w for w in words if w[4] == "PREVISTO"]
    if not previsto:
        raise LayoutError("cabeçalho da grade ('PREVISTO') não encontrado")
    return sum(_yc(w) for w in previsto) / len(previsto)


def _calibrate_columns(words: list[tuple], header_yc: float) -> list[tuple[str, float, float]]:
    hdr = [
        w for w in words
        if abs(_yc(w) - header_yc) < 0.5 and not re.match(r"^[12]$", w[4])
    ]
    row = sorted(hdr, key=_xc)
    names = ["dia", "previsto"]
    for w in row[2:]:
        nome = HEADER_COL_NAMES.get(w[4])
        if nome:
            names.append(nome)
        elif w[4] == "ENT.":
            names.append("ent1" if "ent1" not in names else "ent2")
        elif w[4] == "SAÍ.":
            names.append("sai1" if "sai1" not in names else "sai2")
    if len(names) != len(row):
        raise LayoutError(
            f"cabeçalho da grade 'Cartão de Ponto' incompleto ou inesperado: {[w[4] for w in row]}"
        )

    centers = [_xc(w) for w in row]
    limites = [(a + b) / 2 for a, b in zip(centers, centers[1:])]
    faixas: list[tuple[str, float, float]] = []
    inicio = 0.0
    for nome, fim in zip(names, [*limites, centers[-1] + 25]):
        faixas.append((nome, inicio, fim))
        inicio = fim
    return faixas


def _col_for(xc: float, faixas: list[tuple[str, float, float]]) -> str | None:
    for nome, ini, fim in faixas:
        if ini <= xc < fim:
            return nome
    return None


TIME_COLS = ("ent1", "sai1", "ent2", "sai2")
TEXT_COLS = ("previsto", "ent1", "sai1", "ent2", "sai2")
TOTAL_COLS = ("total_normais", "total_noturno", "dia_falta", "falta_atraso", "abono", "extra_0", "extra_50", "extra_100")


def _classify_day(reason_tokens: list[str], reason_text: str, real_times: dict[str, str], weekday: str) -> PointStatus:
    n_real = len(real_times)

    if "Falta" in reason_tokens:
        return PointStatus.FALTA_PARCIAL if n_real else PointStatus.FALTA_INTEGRAL
    if "Férias" in reason_tokens:
        return PointStatus.FERIAS
    if "Médic" in reason_text:
        return PointStatus.ATESTADO_PARCIAL if n_real else PointStatus.ATESTADO_INTEGRAL
    if "Abonar" in reason_text:
        return PointStatus.ATESTADO_PARCIAL if n_real else PointStatus.ATESTADO_INTEGRAL
    if "Folga" in reason_tokens:
        return PointStatus.DOMINGO
    if n_real == 0 and "FERIADO" in reason_tokens:
        return PointStatus.FERIADO
    if n_real:
        return PointStatus.MARCACAO_IMPAR if n_real % 2 == 1 else PointStatus.TRABALHADO

    return PointStatus.DOMINGO if weekday.upper() in ("SAB", "DOM") else PointStatus.FALTA_INTEGRAL


def _parse_day_rows(words: list[tuple], faixas: list[tuple[str, float, float]]) -> list[dict]:
    anchors = [w for w in words if FULL_DATE_RE.match(w[4]) and w[0] < 70 and w[1] > 169]
    records = []
    for a in sorted(anchors, key=lambda w: w[1]):
        yc_a = _yc(a)
        weekday = ""
        for w in words:
            if 65 < w[0] < 100 and abs(_yc(w) - yc_a) < 4 and w[4] in ("SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"):
                weekday = w[4]
                break

        cells: dict[str, list[str]] = {}
        for w in words:
            if w is a or w[0] < 100 or abs(_yc(w) - yc_a) >= 4:
                continue
            if PAREN_TAG_RE.match(w[4]):
                continue
            col = _col_for(_xc(w), faixas)
            if col:
                cells.setdefault(col, []).append(w[4])

        real_times = {c: cells[c][0] for c in TIME_COLS if cells.get(c) and TIME_RE.match(cells[c][0])}
        reason_tokens = [
            tok for col in TEXT_COLS for tok in cells.get(col, [])
            if not TIME_RE.match(tok) and tok not in ("Feriado:",)
        ]
        reason_text = clean_text(" ".join(reason_tokens))

        status = _classify_day(reason_tokens, reason_text, real_times, weekday)

        totals = {
            name: to_minutes(cells[name][0]) if cells.get(name) and re.match(r"^-?\d{1,3}:\d{2}$", cells[name][0]) else 0
            for name in TOTAL_COLS
        }
        dia_falta_flag = bool(cells.get("dia_falta"))

        worked_min = totals["total_normais"]
        discounted_min = totals["falta_atraso"]

        record = {
            "date": a[4],
            "weekday": weekday,
            "extra_before_entry": "",
            "extra_before_exit": "",
            "first_period_entry": real_times.get("ent1", ""),
            "first_period_exit": real_times.get("sai1", ""),
            "second_period_entry": real_times.get("ent2", ""),
            "second_period_exit": real_times.get("sai2", ""),
            "extra_after_entry": "",
            "extra_after_exit": "",
            "occurrence": reason_text if (status != PointStatus.TRABALHADO or "FERIADO" in reason_tokens) else "",
            "reason": reason_text,
            "worked_minutes": worked_min,
            "discounted_minutes": discounted_min,
            "schedule": [],
            "status": status,
            "lost_weekly_rest": status == PointStatus.DOMINGO and dia_falta_flag,
            "_totals": totals,
        }
        records.append(record)
    return records


def parse_employee_page_cartao(page_text: str, words: list[tuple]) -> dict:
    lines = page_text.split("\n")

    name = extract_labeled_field(lines, ["NOME DO FUNCIONÁRIO", "NOME DO FUNCIONARIO"])
    cpf_raw = extract_labeled_field(lines, ["CPF DO FUNCIONÁRIO", "CPF DO FUNCIONARIO"])
    role = extract_labeled_field(lines, ["NOME DO CARGO"])
    admission = extract_labeled_field(lines, ["DATA DE ADMISSÃO DO FUNCIONÁRIO", "DATA DE ADMISSAO DO FUNCIONARIO"])
    sector_description = extract_labeled_field(lines, ["NOME DO DEPARTAMENTO"])
    matricula = extract_labeled_field(lines, ["NÚMERO DE MATRÍCULA", "NUMERO DE MATRICULA"])

    company_name = extract_labeled_field(lines, ["NOME DA EMPRESA"])
    company_cnpj_raw = extract_labeled_field(lines, ["CNPJ DA EMPRESA"])
    company_cnpj = re.sub(r"\D", "", company_cnpj_raw)
    cpf = re.sub(r"\D", "", cpf_raw)

    period_start = period_end = ""
    for line in lines:
        m = PERIOD_RE.search(line)
        if m:
            period_start, period_end = m.group(1), m.group(2)
            break

    if not name and not cpf:
        return {"name": "", "cpf": ""}

    header_yc = _find_header_yc(words)
    faixas = _calibrate_columns(words, header_yc)
    records = _parse_day_rows(words, faixas)

    worked_minutes_total = sum(r["worked_minutes"] for r in records)
    night_total = sum(r["_totals"]["total_noturno"] for r in records)
    delays_total = sum(r["_totals"]["falta_atraso"] for r in records if r["status"] not in (PointStatus.FALTA_INTEGRAL, PointStatus.FALTA_PARCIAL))
    absences_discounted_total = sum(r["_totals"]["falta_atraso"] for r in records if r["status"] in (PointStatus.FALTA_INTEGRAL, PointStatus.FALTA_PARCIAL))
    overtime_50_total = sum(r["_totals"]["extra_50"] for r in records)
    overtime_100_total = sum(r["_totals"]["extra_100"] for r in records)
    for r in records:
        r.pop("_totals")

    worked_days = sum(1 for r in records if r["status"] == PointStatus.TRABALHADO)
    days_off = sum(1 for r in records if r["status"] in (PointStatus.DOMINGO, PointStatus.SABADO))
    vacation_days = sum(1 for r in records if r["status"] == PointStatus.FERIAS)
    medical_days = sum(1 for r in records if r["status"] in (PointStatus.ATESTADO_INTEGRAL, PointStatus.ATESTADO_PARCIAL))
    absence_days = sum(1 for r in records if r["status"] in (PointStatus.FALTA_INTEGRAL, PointStatus.FALTA_PARCIAL))
    inconsistencies = sum(1 for r in records if r["status"] == PointStatus.MARCACAO_IMPAR)

    summary = {
        "worked_days": worked_days,
        "days_off": days_off,
        "vacation_days": vacation_days,
        "absence_days": absence_days,
        "medical_days": medical_days,
        "inconsistencies": inconsistencies,
        "night_additional_total": minutes_to_time(night_total),
        "normal_hours": minutes_to_time(worked_minutes_total),
        "dsr_normal": "00:00",
        "weekly_total": "00:00",
        "saldo_banco": "00:00",
        "discounted_total": minutes_to_time(delays_total + absences_discounted_total),
        "worked_hours_paid": minutes_to_time(worked_minutes_total),
        "dsr_paid": "00:00",
        "dsr_discount": "00:00",
        "delays": minutes_to_time(delays_total),
        "absences_paid": "00:00",
        "absences_discounted": minutes_to_time(absences_discounted_total),
        "early_departures": "00:00",
        "overtime_50": minutes_to_time(overtime_50_total),
        "overtime_70": "00:00",
        "overtime_100": minutes_to_time(overtime_100_total),
    }

    checksums = {
        "ck_trab": True,
        "ck_desc": True,
    }

    return {
        "id": str(uuid.uuid4()),
        "matricula": matricula,
        "name": name,
        "cpf": cpf,
        "role": role,
        "sector_code": "",
        "sector_description": sector_description,
        "schedule_label": "",
        "admission": admission,
        "records": records,
        "summary": summary,
        "checksums": checksums,
        "company_name": company_name,
        "company_cnpj": company_cnpj,
        "period_start": period_start,
        "period_end": period_end,
    }
