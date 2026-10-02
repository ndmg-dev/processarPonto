import re
import uuid
from app.models.schemas import PointStatus
from app.services.classifier import classify_day, OCORRENCIAS

# Layout "Acesso Relógio de Ponto Digital v.4.5.153" — ver
# reestruturacao-processar-ponto.md §2 e §5. As posições abaixo NÃO são
# faixas fixas: tudo que é coluna de grade/resumo é calibrado a partir das
# palavras do próprio cabeçalho em cada página, porque pequenas variações de
# fonte/margem entre páginas (ou entre arquivos) deslocam as coordenadas o
# suficiente pra quebrar faixas fixas. Faixas fixas foram exatamente a causa
# da versão anterior deste parser classificar tudo como FALTA.

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
TOTAL_TIME_RE = re.compile(r"^-?\d{1,3}:\d{2}$")
DATE_RE = re.compile(r"^\d{2}/\d{2}$")
WEEKDAY_RE = re.compile(r"^(Seg|Ter|Qua|Qui|Sex|Sab|S[áa]b|Dom)$", re.IGNORECASE)
MATRICULA_RE = re.compile(r"^\d{8}$")

SLOT_NAMES = (
    "extra_before_entry", "extra_before_exit",
    "first_period_entry", "first_period_exit",
    "second_period_entry", "second_period_exit",
    "extra_after_entry", "extra_after_exit",
)


class LayoutError(Exception):
    """Layout não reconhecido — nunca "tentamos a sorte" com faixas fixas;
    se o cabeçalho esperado não aparece, paramos com erro explícito."""


def to_minutes(value: str) -> int:
    if not value:
        return 0
    neg = value.startswith("-")
    h, m = value.lstrip("-").split(":")
    total = int(h) * 60 + int(m)
    return -total if neg else total


def minutes_to_time(total: int) -> str:
    neg = total < 0
    total = abs(total)
    h, m = divmod(total, 60)
    s = f"{h:02d}:{m:02d}"
    return f"-{s}" if neg else s


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _xc(w: tuple) -> float:
    return (w[0] + w[2]) / 2


def _yc(w: tuple) -> float:
    return (w[1] + w[3]) / 2


def extract_labeled_field(lines: list[str], label_variants: list[str]) -> str:
    """Extrai campos "Rótulo : Valor" do cabeçalho — às vezes na mesma linha
    de texto, às vezes com rótulo/":"/valor em linhas separadas."""
    pattern = "|".join(label_variants)
    for i, line in enumerate(lines):
        cleaned = clean_text(line)
        m = re.match(rf"^(?:{pattern})\s*:\s*(.+)$", cleaned, re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip()
        if re.match(rf"^(?:{pattern})$", cleaned, re.IGNORECASE):
            j = i + 1
            while j < len(lines) and clean_text(lines[j]) == ":":
                j += 1
            if j < len(lines):
                value = clean_text(lines[j])
                if value and value != ":":
                    return value
    return ""


def find_header_yc(words: list[tuple]) -> float:
    ini_words = [w for w in words if w[4] == "Ini"]
    if not ini_words:
        raise LayoutError("cabeçalho da grade ('Ini') não encontrado")
    return sum(_yc(w) for w in ini_words) / len(ini_words)


def calibrate_columns(words: list[tuple], header_yc: float) -> list[tuple[str, float, float]]:
    """Deriva as faixas de x da grade diária a partir da posição real das
    palavras Ini/Fim/Trab/Desc do cabeçalho — nunca de constantes fixas."""
    names = list(SLOT_NAMES) + ["worked_minutes", "discounted_minutes"]
    hdr = [w for w in words if w[4] in ("Ini", "Fim", "Trab", "Desc") and abs(_yc(w) - header_yc) < 3]
    if len(hdr) != len(names):
        raise LayoutError(
            f"esperado {len(names)} colunas de cabeçalho (Ini/Fim/Trab/Desc), encontrado {len(hdr)}"
        )
    row = sorted(hdr, key=_xc)
    centers = [_xc(w) for w in row]
    limites = [(a + b) / 2 for a, b in zip(centers, centers[1:])]

    faixas: list[tuple[str, float, float]] = []
    inicio = 85.0  # abaixo disso ficam só weekday/data, nunca célula de dia
    for nome, fim in zip(names, [*limites, centers[-1] + 20]):
        faixas.append((nome, inicio, fim))
        inicio = fim
    faixas.append(("quadro", inicio, 10_000.0))
    return faixas


def _col_for(xc: float, faixas: list[tuple[str, float, float]]) -> str | None:
    for nome, ini, fim in faixas:
        if ini <= xc < fim:
            return nome
    return None


def _first_time(tokens: list[str]) -> int:
    for t in tokens:
        if TOTAL_TIME_RE.match(t):
            return to_minutes(t)
    return 0


def parse_day_rows(words: list[tuple], faixas: list[tuple[str, float, float]], header_yc: float) -> list[dict]:
    anchors = [
        w for w in words
        if DATE_RE.match(w[4]) and w[0] < 90 and w[1] > header_yc + 5
    ]
    records = []
    for a in sorted(anchors, key=lambda w: w[1]):
        yc_a = _yc(a)

        weekday = ""
        for w in words:
            if w[0] < 45 and abs(_yc(w) - yc_a) < 5 and WEEKDAY_RE.match(w[4]):
                weekday = w[4]
                break

        cells: dict[str, list[str]] = {}
        for w in words:
            if w is a or w[0] < 85 or abs(_yc(w) - yc_a) >= 3:
                continue
            col = _col_for(_xc(w), faixas)
            if col:
                cells.setdefault(col, []).append(w[4])

        marcacoes: dict[str, str] = {}
        ocorrencias: dict[str, str] = {}
        for slot in SLOT_NAMES:
            toks = cells.get(slot, [])
            if not toks:
                continue
            val = toks[0]
            if TIME_RE.match(val):
                marcacoes[slot] = val
            elif val in OCORRENCIAS:
                ocorrencias[slot] = val

        worked_min = _first_time(cells.get("worked_minutes", []))
        discounted_min = _first_time(cells.get("discounted_minutes", []))
        quadro_tokens = cells.get("quadro", [])

        classify_input = {
            "quadro": quadro_tokens,
            "ocorrencias": ocorrencias,
            "horas_trab_min": worked_min,
            "horas_desc_min": discounted_min,
            "n_marcacoes": len(marcacoes),
        }
        status = classify_day(classify_input)
        lost_weekly_rest = status in (PointStatus.DOMINGO, PointStatus.SABADO) and discounted_min > 0

        record = {slot: marcacoes.get(slot, "") for slot in SLOT_NAMES}
        record.update({
            "date": a[4],
            "weekday": weekday,
            "occurrence": " ".join(sorted(set(ocorrencias.values()))),
            "reason": "",
            "worked_minutes": worked_min,
            "discounted_minutes": discounted_min,
            "schedule": quadro_tokens,
            "status": status,
            "lost_weekly_rest": lost_weekly_rest,
        })
        records.append(record)
    return records


def extract_resumo_fields(words: list[tuple]) -> dict:
    """Bloco RESUMO (rodapé): bloco superior de valor único (Horas Normais,
    DSR Normais, Total Semanal, Saldo Banc., Adc Noturno, Tot Descontado,
    Extra A 050/070/100%) e bloco inferior com colunas Pagos/Desc. separadas
    (H. Trab., DSR, Atrasos, Faltas, Saídas Antecipada). A coluna de cada
    valor é sempre lida pela coordenada, nunca pela ordem dos tokens —
    "DSR 07:2022:00" só faz sentido com a posição x de cada parte."""
    fields = {
        "normal_hours": "00:00", "dsr_normal": "00:00", "weekly_total": "00:00",
        "saldo_banco": "00:00", "night_additional_total": "00:00", "discounted_total": "00:00",
        "worked_hours_paid": "00:00", "dsr_paid": "00:00", "dsr_discount": "00:00",
        "delays": "00:00", "absences_paid": "00:00", "absences_discounted": "00:00",
        "early_departures": "00:00", "overtime_50": "00:00", "overtime_70": "00:00", "overtime_100": "00:00",
    }

    resumo_y = next((w[1] for w in words if w[4] == "RESUMO"), None)
    if resumo_y is None:
        raise LayoutError("bloco 'RESUMO' não encontrado")
    rw = [w for w in words if w[1] >= resumo_y - 2]

    pagos_x = next((w[0] for w in rw if w[4] == "Pagos"), None)
    desc_x = next((w[0] for w in rw if w[4] == "Desc."), None)
    if pagos_x is None or desc_x is None:
        raise LayoutError("cabeçalho 'Pagos'/'Desc.' do RESUMO não encontrado")

    pagos_y0 = next(w[1] for w in rw if w[4] == "Pagos")
    upper = [w for w in rw if w[1] < pagos_y0 - 5]
    lower = [w for w in rw if w[1] >= pagos_y0 - 5]

    col_a_value = 140.0

    def value_at(pool: list[tuple], label_text: str, target_x: float, y_tol: float = 2.0, max_dx: float = 30.0):
        """Pega, na mesma linha do rótulo, o valor numérico mais PRÓXIMO de
        target_x — nunca o primeiro token "dentro de uma faixa", porque a
        ordem de leitura do PyMuPDF segue blocos/colunas internos do PDF, não
        necessariamente esquerda->direita entre as colunas Pagos/Desc."""
        label_y = next((w[1] for w in pool if w[4] == label_text), None)
        if label_y is None:
            return None
        candidatos = [
            w for w in pool
            if abs(w[1] - label_y) < y_tol and TOTAL_TIME_RE.match(w[4])
        ]
        if not candidatos:
            return "00:00"
        melhor = min(candidatos, key=lambda w: abs(w[0] - target_x))
        return melhor[4] if abs(melhor[0] - target_x) <= max_dx else "00:00"

    if (v := value_at(upper, "Horas", col_a_value)) is not None:
        fields["normal_hours"] = v
    if (v := value_at(upper, "DSR", col_a_value)) is not None:
        fields["dsr_normal"] = v
    if (v := value_at(upper, "Total", col_a_value)) is not None:
        fields["weekly_total"] = v
    if (v := value_at(upper, "Saldo", col_a_value)) is not None:
        fields["saldo_banco"] = v
    if (v := value_at(upper, "Adc", col_a_value)) is not None:
        fields["night_additional_total"] = v
    if (v := value_at(upper, "Tot", col_a_value)) is not None:
        fields["discounted_total"] = v

    if (v := value_at(lower, "H.", pagos_x)) is not None:
        fields["worked_hours_paid"] = v
    if (v := value_at(lower, "DSR", pagos_x)) is not None:
        fields["dsr_paid"] = v
    if (v := value_at(lower, "DSR", desc_x)) is not None:
        fields["dsr_discount"] = v
    if (v := value_at(lower, "Atrasos", desc_x)) is not None:
        fields["delays"] = v
    if (v := value_at(lower, "Faltas", pagos_x)) is not None:
        fields["absences_paid"] = v
    if (v := value_at(lower, "Faltas", desc_x)) is not None:
        fields["absences_discounted"] = v
    if (v := value_at(lower, "Saídas", desc_x)) is not None:
        fields["early_departures"] = v

    # "Extra A 050%" / "Extra A 070%" / "Extra A 100%" — sempre as mesmas 3
    # linhas, uma abaixo da outra, no bloco superior.
    extra_keys = {"050%": "overtime_50", "070%": "overtime_70", "100%": "overtime_100"}
    a_words = sorted((w for w in upper if w[4] == "A" and 210 <= w[0] <= 232), key=lambda w: w[1])
    for a_word in a_words:
        pct_word = next((w for w in upper if w[4] in extra_keys and abs(w[1] - a_word[1]) < 2), None)
        if not pct_word:
            continue
        val = next(
            (w[4] for w in upper if w[0] > 245 and abs(w[1] - a_word[1]) < 2 and TOTAL_TIME_RE.match(w[4])),
            "00:00",
        )
        fields[extra_keys[pct_word[4]]] = val

    return fields


def parse_employee_page(page_text: str, words: list[tuple]) -> dict:
    lines = page_text.split("\n")

    name = extract_labeled_field(lines, ["Funcionário", "Funcionario"])
    cpf = extract_labeled_field(lines, ["CPF"])
    role = extract_labeled_field(lines, ["Cargo"])
    admission = extract_labeled_field(lines, ["Admissão", "Admissao"])
    sector_raw = extract_labeled_field(lines, ["Setor"])
    schedule_label = extract_labeled_field(lines, ["Horário", "Horario"])

    sector_code, _, sector_description = sector_raw.partition(" ")
    if not sector_description:
        sector_description, sector_code = sector_code, ""

    # A matrícula (8 dígitos) fica na mesma linha do nome, à esquerda dele —
    # não existe em campo de texto isolado e confiável neste layout.
    matricula = next(
        (w[4] for w in words if MATRICULA_RE.match(w[4]) and w[1] < 120),
        "",
    )

    if not name and not cpf:
        # Página sem dados de colaborador — não é erro de layout, só uma
        # página em branco/intermediária; parse_pdf_pages descarta.
        return {"name": "", "cpf": ""}

    header_yc = find_header_yc(words)
    faixas = calibrate_columns(words, header_yc)
    records = parse_day_rows(words, faixas, header_yc)
    summary = extract_resumo_fields(words)

    worked_minutes_total = sum(r["worked_minutes"] for r in records)
    discounted_minutes_total = sum(r["discounted_minutes"] for r in records)

    worked_days = sum(1 for r in records if r["status"] == PointStatus.TRABALHADO)
    days_off = sum(1 for r in records if r["status"] in (PointStatus.DOMINGO, PointStatus.SABADO))
    medical_days = sum(1 for r in records if r["status"] in (PointStatus.ATESTADO_INTEGRAL, PointStatus.ATESTADO_PARCIAL))
    absence_days = sum(1 for r in records if r["status"] in (PointStatus.FALTA_INTEGRAL, PointStatus.FALTA_PARCIAL))
    inconsistencies = sum(1 for r in records if r["status"] == PointStatus.MARCACAO_IMPAR)

    summary.update({
        "worked_days": worked_days,
        "days_off": days_off,
        "vacation_days": 0,
        "absence_days": absence_days,
        "medical_days": medical_days,
        "inconsistencies": inconsistencies,
    })

    # Checksums (§6.1) — só calculados e expostos por enquanto; bloquear o
    # envio quando algum falhar é de uma fase posterior (API/pendências).
    desc_resumo_total = (
        to_minutes(summary["dsr_discount"])
        + to_minutes(summary["delays"])
        + to_minutes(summary["absences_discounted"])
        + to_minutes(summary["early_departures"])
    )
    checksums = {
        "ck_trab": to_minutes(summary["worked_hours_paid"]) == worked_minutes_total,
        "ck_desc": desc_resumo_total == discounted_minutes_total,
    }

    return {
        "id": str(uuid.uuid4()),
        "matricula": matricula,
        "name": name,
        "cpf": cpf,
        "role": role,
        "sector_code": sector_code,
        "sector_description": sector_description,
        "schedule_label": schedule_label,
        "admission": admission,
        "records": records,
        "summary": summary,
        "checksums": checksums,
    }


def parse_pdf_pages(pages: list[str], pages_words: list[list[tuple]]) -> list[dict]:
    employees = []
    for page_text, words in zip(pages, pages_words):
        if not page_text.strip():
            continue
        emp_data = parse_employee_page(page_text, words)
        if emp_data["name"] or emp_data["cpf"]:
            employees.append(emp_data)
    return employees
