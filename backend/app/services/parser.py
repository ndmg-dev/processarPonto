import re
from app.services.classifier import classify_record
from app.models.schemas import PointStatus

CPF_REGEX = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
TIME_REGEX = r"^\d{2}:\d{2}$"
# Totais acumulados (ex: "188:00", "012:11") podem ter 3 dígitos de hora.
TOTAL_TIME_REGEX = r"^\d{2,3}:\d{2}$"
WEEKDAY_REGEX = r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)$"
DATE_REGEX = r"^\d{2}/\d{2}$"
SCHEDULE_MAP_REGEX = r"(\d{4})\s+-\s+((?:\d{2}:\d{2}\s*)+)"

# Faixas de coordenada X (em pontos) das colunas do "Espelho de Ponto Eletrônico".
# O texto extraído célula-a-célula não preserva a ordem lógica das colunas,
# então cada campo do dia é localizado pela posição horizontal na página.
COL_EXTRA1 = (165, 216)
COL_PERIOD1 = (216, 270)
COL_PERIOD2 = (270, 322)
COL_EXTRA2 = (322, 366)
COL_SCHEDULE_CODE = (366, 405)
COL_OCCURRENCE = (505, 533)
COL_REASON_MIN = 533

NIGHT_ADDITIONAL_VALUE_X = (115, 155)

# Faixas de coordenada X do bloco "RESUMO" no rodapé do espelho. O bloco tem
# três colunas de rótulo (A, B, C), cada uma com sua(s) coluna(s) de valor à
# direita, alinhadas por Y com o respectivo rótulo.
RESUMO_COL_A_LABEL_X = (25, 90)
RESUMO_COL_A_VALUE_X = (115, 165)

RESUMO_COL_B_LABEL_X = (180, 250)
RESUMO_COL_B_PAGOS_X = (255, 295)
RESUMO_COL_B_DESC_X = (295, 330)

RESUMO_COL_C_LABEL_X = (340, 390)
RESUMO_COL_C_VALUE_X = (385, 420)

def time_to_minutes(time_str: str) -> int:
    if not time_str:
        return 0
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)

def minutes_to_time(total_minutes: int) -> str:
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def parse_schedule_map(text: str) -> dict:
    schedule_map = {}
    for line in text.split("\n"):
        matches = re.findall(SCHEDULE_MAP_REGEX, line)
        for code, times_str in matches:
            times = re.findall(r"\d{2}:\d{2}", times_str)
            schedule_map[code] = times
    return schedule_map

def extract_labeled_field(lines: list[str], label_variants: list[str]) -> str:
    """
    Extrai campos do tipo "Rótulo : Valor" do cabeçalho do espelho de ponto.
    No PDF, rótulo, ":" e valor às vezes vêm na mesma linha de texto (ex: "CPF :
    103.077.514-14") e às vezes em linhas separadas (ex: "Funcionário" / ":" /
    "NOME"), então tentamos os dois formatos.
    """
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

def extract_night_additional_total(words: list[tuple]) -> str:
    """
    O "Adc Noturno" aparece no bloco RESUMO como rótulo ("Adc" + "Noturno") e o
    valor correspondente fica na mesma altura (y), numa coluna de valores à
    direita. Quando o total é zero a célula fica em branco e nenhuma palavra é
    encontrada nessa linha.
    """
    label_y = None
    for w in words:
        if w[4] == "Adc":
            label_y = w[1]
            break
    if label_y is None:
        return "00:00"

    for w in words:
        x0, y0, text = w[0], w[1], w[4]
        if NIGHT_ADDITIONAL_VALUE_X[0] <= x0 <= NIGHT_ADDITIONAL_VALUE_X[1] and abs(y0 - label_y) < 1.5:
            if re.match(TOTAL_TIME_REGEX, text):
                return text
    return "00:00"

def _extract_field_value(words: list[tuple], label_y: float, value_x_range: tuple, y_tolerance: float = 2.0) -> str:
    for w in words:
        x0, y0, text = w[0], w[1], w[4]
        if value_x_range[0] <= x0 <= value_x_range[1] and abs(y0 - label_y) < y_tolerance:
            if re.match(TOTAL_TIME_REGEX, text):
                return text
    return "00:00"

def _extract_label_text(words: list[tuple], label_y: float, x_range: tuple, y_tolerance: float = 2.0) -> str:
    """
    Reconstrói o texto do rótulo (ex: "H.E. 100%", "H.E. A 050%") juntando as
    palavras da linha dentro da faixa X do rótulo, ignorando o ":" separador.
    """
    row_words = [
        w for w in words
        if x_range[0] <= w[0] <= x_range[1] and abs(w[1] - label_y) < y_tolerance and w[4] != ":"
    ]
    return " ".join(w[4] for w in sorted(row_words, key=lambda w: w[0]))

def _find_label_y(words: list[tuple], label_text: str, x_range: tuple, y_min: float = None, y_max: float = None) -> float | None:
    for w in words:
        x0, y0, text = w[0], w[1], w[4]
        if text != label_text:
            continue
        if not (x_range[0] <= x0 <= x_range[1]):
            continue
        if y_min is not None and y0 < y_min:
            continue
        if y_max is not None and y0 > y_max:
            continue
        return y0
    return None

def extract_resumo_fields(words: list[tuple]) -> dict:
    """
    Extrai os campos do bloco "RESUMO" no rodapé do espelho de ponto (Horas
    Normais, DSR Normais, Total Semanal, Tot Descontado, H. Trab./DSR/Atrasos/
    Faltas/Saídas Antecipadas em Pagos e Desc., H.E. 050% e a segunda linha de
    hora extra, cujo rótulo varia por colaborador/período: "H.E. A 050%" ou
    "H.E. 100%"). Assim como o Adc Noturno, cada rótulo tem seu valor correspondente na
    mesma altura (Y), numa coluna de valores à direita; quando o valor é zero
    a célula fica em branco e o campo retorna "00:00".
    """
    fields = {
        "normal_hours": "00:00",
        "dsr_normal": "00:00",
        "weekly_total": "00:00",
        "discounted_total": "00:00",
        "worked_hours_paid": "00:00",
        "dsr_paid": "00:00",
        "dsr_discount": "00:00",
        "delays": "00:00",
        "absences_time": "00:00",
        "early_departures": "00:00",
        "overtime_50": "00:00",
        "overtime_extra_label": "",
        "overtime_extra_value": "00:00",
    }

    resumo_y = None
    for w in words:
        if w[4] == "RESUMO":
            resumo_y = w[1]
            break
    if resumo_y is None:
        return fields

    # Só considera palavras a partir do início do bloco RESUMO, para não
    # colidir com rótulos homônimos usados em outras partes do espelho.
    resumo_words = [w for w in words if w[1] >= resumo_y - 2]

    # Coluna A (rótulo à esquerda / valor único à direita)
    if (y := _find_label_y(resumo_words, "Horas", RESUMO_COL_A_LABEL_X)) is not None:
        fields["normal_hours"] = _extract_field_value(resumo_words, y, RESUMO_COL_A_VALUE_X)
    if (y := _find_label_y(resumo_words, "DSR", RESUMO_COL_A_LABEL_X)) is not None:
        fields["dsr_normal"] = _extract_field_value(resumo_words, y, RESUMO_COL_A_VALUE_X)
    if (y := _find_label_y(resumo_words, "Total", RESUMO_COL_A_LABEL_X)) is not None:
        fields["weekly_total"] = _extract_field_value(resumo_words, y, RESUMO_COL_A_VALUE_X)
    if (y := _find_label_y(resumo_words, "Tot", RESUMO_COL_A_LABEL_X)) is not None:
        fields["discounted_total"] = _extract_field_value(resumo_words, y, RESUMO_COL_A_VALUE_X)

    # Coluna B (rótulo central / colunas de valor "Pagos" e "Desc." à direita)
    if (y := _find_label_y(resumo_words, "H.", RESUMO_COL_B_LABEL_X)) is not None:
        fields["worked_hours_paid"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_PAGOS_X)
    if (y := _find_label_y(resumo_words, "DSR", RESUMO_COL_B_LABEL_X)) is not None:
        fields["dsr_paid"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_PAGOS_X)
        fields["dsr_discount"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_DESC_X)
    if (y := _find_label_y(resumo_words, "Atrasos", RESUMO_COL_B_LABEL_X)) is not None:
        fields["delays"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_DESC_X)
    if (y := _find_label_y(resumo_words, "Faltas", RESUMO_COL_B_LABEL_X)) is not None:
        fields["absences_time"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_DESC_X)
    if (y := _find_label_y(resumo_words, "Saídas", RESUMO_COL_B_LABEL_X)) is not None:
        fields["early_departures"] = _extract_field_value(resumo_words, y, RESUMO_COL_B_DESC_X)

    # Coluna C (Horas Extras). A primeira linha é sempre "H.E. 050%"; a
    # segunda linha (quando existe) varia entre "H.E. A 050%" e "H.E. 100%"
    # conforme o colaborador/período, então o rótulo é lido dinamicamente em
    # vez de fixado.
    if (y := _find_label_y(resumo_words, "H.E.", RESUMO_COL_C_LABEL_X)) is not None:
        fields["overtime_50"] = _extract_field_value(resumo_words, y, RESUMO_COL_C_VALUE_X)
        if (y2 := _find_label_y(resumo_words, "H.E.", RESUMO_COL_C_LABEL_X, y_min=y + 5)) is not None:
            fields["overtime_extra_value"] = _extract_field_value(resumo_words, y2, RESUMO_COL_C_VALUE_X)
            fields["overtime_extra_label"] = _extract_label_text(resumo_words, y2, RESUMO_COL_C_LABEL_X)

    return fields

def group_words_into_rows(words: list[tuple], y_tolerance: float = 3.0) -> list[list[tuple]]:
    sorted_words = sorted(words, key=lambda w: (w[1], w[0]))
    rows = []
    current_row = []
    current_y = None
    for w in sorted_words:
        y = w[1]
        if current_y is None or abs(y - current_y) <= y_tolerance:
            current_row.append(w)
            current_y = y if current_y is None else current_y
        else:
            rows.append(current_row)
            current_row = [w]
            current_y = y
    if current_row:
        rows.append(current_row)
    return rows

def words_in_range(row: list[tuple], x_min: float, x_max: float) -> list[str]:
    return [w[4] for w in sorted(row, key=lambda w: w[0]) if x_min <= w[0] < x_max]

def entry_exit_from_bucket(texts: list[str]) -> tuple[str, str]:
    times = [t for t in texts if re.match(TIME_REGEX, t)]
    entry = times[0] if len(times) >= 1 else ""
    exit_ = times[1] if len(times) >= 2 else ""
    return entry, exit_

def parse_day_rows(words: list[tuple], schedule_map: dict) -> list[dict]:
    rows = group_words_into_rows(words)
    records = []

    for row in rows:
        weekday = ""
        date_str = ""
        for w in sorted(row, key=lambda w: w[0]):
            if not weekday and w[0] < 45 and re.match(WEEKDAY_REGEX, w[4]):
                weekday = w[4]
            elif not date_str and 45 <= w[0] < 70 and re.match(DATE_REGEX, w[4]):
                date_str = w[4]

        if not weekday or not date_str:
            continue

        extra1_texts = words_in_range(row, *COL_EXTRA1)
        p1_texts = words_in_range(row, *COL_PERIOD1)
        p2_texts = words_in_range(row, *COL_PERIOD2)
        extra2_texts = words_in_range(row, *COL_EXTRA2)

        first_entry, first_exit = entry_exit_from_bucket(p1_texts)
        second_entry, second_exit = entry_exit_from_bucket(p2_texts)

        # Dias inteiros (Folga, Domingo, Férias, Atestado, etc.) aparecem como uma
        # palavra-chave repetida nas colunas de horário, em vez de horários reais.
        keyword_texts = [
            t for t in (extra1_texts + p1_texts + p2_texts + extra2_texts)
            if not re.match(TIME_REGEX, t)
        ]

        schedule_code = ""
        for t in words_in_range(row, *COL_SCHEDULE_CODE):
            if re.match(r"^\d{4}$", t):
                schedule_code = t
                break

        occurrence = " ".join(words_in_range(row, *COL_OCCURRENCE))

        reason_words = [w[4] for w in sorted(row, key=lambda w: w[0]) if w[0] >= COL_REASON_MIN]
        reason = clean_text(" ".join(reason_words))
        if not reason and keyword_texts:
            # Remove repetições (ex: "FOL FOL FOL FOL" -> "FOL")
            seen = []
            for kw in keyword_texts:
                if kw not in seen:
                    seen.append(kw)
            reason = " ".join(seen)

        record = {
            "date": date_str,
            "weekday": weekday,
            "first_period_entry": first_entry,
            "first_period_exit": first_exit,
            "second_period_entry": second_entry,
            "second_period_exit": second_exit,
            "occurrence": occurrence,
            "reason": reason,
            "schedule_code": schedule_code,
        }

        classified = classify_record(record, schedule_map)
        records.append(classified)

    return records

def parse_employee_page(page_text: str, words: list[tuple]) -> dict:
    lines = page_text.split("\n")

    employee = {
        "id": "",
        "name": "",
        "cpf": "",
        "role": "",
        "records": [],
        "summary": {
            "worked_days": 0,
            "days_off": 0,
            "vacation_days": 0,
            "absence_days": 0,
            "medical_days": 0,
            "inconsistencies": 0,
            "night_additional_total": "00:00",
            "normal_hours": "00:00",
            "dsr_normal": "00:00",
            "weekly_total": "00:00",
            "discounted_total": "00:00",
            "worked_hours_paid": "00:00",
            "dsr_paid": "00:00",
            "dsr_discount": "00:00",
            "delays": "00:00",
            "absences_time": "00:00",
            "early_departures": "00:00",
            "overtime_50": "00:00",
            "overtime_extra_label": "",
            "overtime_extra_value": "00:00"
        }
    }

    employee["name"] = extract_labeled_field(lines, ["Funcionário", "Funcionario"])
    employee["cpf"] = extract_labeled_field(lines, ["CPF"])
    employee["role"] = extract_labeled_field(lines, ["Cargo"])
    # Não há matrícula isolada de forma confiável no espelho; o CPF (único por
    # colaborador) é usado como identificador.
    employee["id"] = re.sub(r"\D", "", employee["cpf"]) or employee["name"]

    schedule_map = parse_schedule_map(page_text)
    employee["records"] = parse_day_rows(words, schedule_map)
    employee["summary"]["night_additional_total"] = extract_night_additional_total(words)
    employee["summary"].update(extract_resumo_fields(words))

    for classified in employee["records"]:
        st = classified["status"]
        if st in [PointStatus.TRABALHADO, PointStatus.TRABALHADO_PARCIAL, PointStatus.TRABALHADO_COM_OCORRENCIA]:
            employee["summary"]["worked_days"] += 1
        elif st in [PointStatus.FOLGA, PointStatus.DOMINGO]:
            employee["summary"]["days_off"] += 1
        elif st == PointStatus.FERIAS:
            employee["summary"]["vacation_days"] += 1
        elif st == PointStatus.ATESTADO:
            employee["summary"]["medical_days"] += 1
        elif st == PointStatus.FALTA:
            employee["summary"]["absence_days"] += 1
        elif st == PointStatus.INCONSISTENCIA:
            employee["summary"]["inconsistencies"] += 1

    return employee

def parse_pdf_pages(pages: list[str], pages_words: list[list[tuple]]) -> list[dict]:
    employees = []
    for page_text, words in zip(pages, pages_words):
        if not page_text.strip():
            continue
        emp_data = parse_employee_page(page_text, words)
        if emp_data["id"] or emp_data["name"]:
            employees.append(emp_data)
    return employees
