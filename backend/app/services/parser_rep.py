"""Variante "Marcações Reg. no REP" da mesma família de layout "ESPELHO DE
PONTO ELETRÔNICO" (mesmo rodapé "JOSE EDUARDO DE JESUS COELHO - ME -
v.4.5.140" — versão diferente da "Acesso Relógio de Ponto Digital
v.4.5.153" que parser.py já suporta). Detectada e tratada à parte porque,
apesar de ter os mesmos 8 slots de horário (Extra/1º/2º/Extra Período),
difere em pontos que importam:

- Cabeçalho da grade usa "Ent"/"Sai" em vez de "Ini"/"Fim".
- Não existem colunas de Horas Trab/Desc por dia — só um código de
  horário (CH) por dia; horas trabalhadas são recalculadas aqui a partir
  dos próprios horários batidos.
- O RESUMO é gravado em "HHH:CC", onde CC são CENTÉSIMOS de hora, não
  minutos (confirmado comparando a soma real dos horários batidos de um
  colaborador do arquivo de referência contra o valor de "H. Trab." do
  resumo — bateu dentro de ~1%, margem explicável por ajustes manuais de
  marcação que este protótipo não modela dia a dia).
- Ocorrências de dia inteiro usam códigos diferentes: FOL (folga,
  American qualquer dia da semana, não só domingo/sábado) e FER
  (feriado), e os motivos de ausência (Atestado Médico, Declaração
  Médica, Férias Descansadas, Ajuste de Marcação) vêm como texto livre
  numa coluna "Tratamentos efetuados", não como código de 3-4 letras na
  própria célula do horário.
"""

import re

from app.models.schemas import PointStatus
from app.services.parser import (
    DATE_RE,
    MATRICULA_RE,
    SLOT_NAMES,
    TIME_RE,
    WEEKDAY_RE,
    LayoutError,
    _xc,
    _yc,
    clean_text,
    extract_labeled_field,
    minutes_to_time,
    to_minutes,
)

CENT_RE = re.compile(r"^-?\d{1,3}:\d{2}$")
CNPJ_RE = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")

WHOLE_DAY_FOLGA = "FOL"
WHOLE_DAY_FERIADO = "FER"
FALTA_WORD = "FALTA"

_PAIR_INDEXES = ((0, 1), (2, 3), (4, 5), (6, 7))


def is_rep_layout(words: list[tuple]) -> bool:
    return any(w[4] == "Ent" for w in words) and not any(w[4] == "Ini" for w in words)


def to_minutes_cent(value: str) -> int:
    if not value:
        return 0
    neg = value.startswith("-")
    h, cc = value.lstrip("-").split(":")
    minutos = round(int(cc) / 100 * 60)
    total = int(h) * 60 + minutos
    return -total if neg else total


def _find_header_yc(words: list[tuple]) -> float:
    ent_words = [w for w in words if w[4] == "Ent"]
    if not ent_words:
        raise LayoutError("cabeçalho da grade ('Ent') não encontrado")
    return sum(_yc(w) for w in ent_words) / len(ent_words)


def _calibrate_columns(words: list[tuple], header_yc: float) -> list[tuple[str, float, float]]:
    hdr = [w for w in words if w[4] in ("Ent", "Sai") and abs(_yc(w) - header_yc) < 3]
    if len(hdr) != len(SLOT_NAMES):
        raise LayoutError(
            f"esperado {len(SLOT_NAMES)} colunas de cabeçalho (Ent/Sai), encontrado {len(hdr)}"
        )
    row = sorted(hdr, key=_xc)
    centers = [_xc(w) for w in row]
    limites = [(a + b) / 2 for a, b in zip(centers, centers[1:])]

    # Diferente do layout original: aqui existe um bloco "Marcações Reg. no
    # REP" (texto bruto, sem sub-colunas) entre a data e a grade
    # "Jornada Realizada" de verdade — por isso a primeira faixa não pode
    # começar logo depois da data (x=85 fixo), senão engole esse bloco
    # inteiro. Usa a largura típica de coluna (distância até a 2ª) pra
    # estimar onde a 1ª coluna de verdade começa.
    largura_tipica = limites[0] - centers[0]
    faixas: list[tuple[str, float, float]] = []
    inicio = centers[0] - largura_tipica
    for nome, fim in zip(SLOT_NAMES, [*limites, centers[-1] + 20]):
        faixas.append((nome, inicio, fim))
        inicio = fim
    faixas.append(("tratamento", inicio, 10_000.0))
    return faixas


def _col_for(xc: float, faixas: list[tuple[str, float, float]]) -> str | None:
    for nome, ini, fim in faixas:
        if ini <= xc < fim:
            return nome
    return None


def _worked_minutes_from_slots(slot_tokens: dict[str, str]) -> int:
    total = 0
    for ini_idx, fim_idx in _PAIR_INDEXES:
        ini_val = slot_tokens.get(SLOT_NAMES[ini_idx])
        fim_val = slot_tokens.get(SLOT_NAMES[fim_idx])
        if ini_val and fim_val and TIME_RE.match(ini_val) and TIME_RE.match(fim_val):
            h1, m1 = map(int, ini_val.split(":"))
            h2, m2 = map(int, fim_val.split(":"))
            total += (h2 * 60 + m2) - (h1 * 60 + m1)
    return max(total, 0)


def _classify_day(slot_tokens: dict[str, str], motivo: str) -> PointStatus:
    populados = list(slot_tokens.values())

    if populados and all(v == WHOLE_DAY_FOLGA for v in populados):
        return PointStatus.DOMINGO
    if populados and all(v == WHOLE_DAY_FERIADO for v in populados):
        return PointStatus.FERIADO
    if "Férias" in motivo:
        return PointStatus.FERIAS
    if "Médic" in motivo:
        return PointStatus.ATESTADO_PARCIAL if FALTA_WORD in populados else PointStatus.ATESTADO_INTEGRAL

    if FALTA_WORD in populados:
        reais = [v for v in populados if TIME_RE.match(v)]
        return PointStatus.FALTA_PARCIAL if reais else PointStatus.FALTA_INTEGRAL

    n_marcacoes = len([v for v in populados if TIME_RE.match(v)])
    if n_marcacoes % 2 == 1:
        return PointStatus.MARCACAO_IMPAR
    return PointStatus.TRABALHADO


def _parse_day_rows(words: list[tuple], faixas: list[tuple[str, float, float]], header_yc: float) -> list[dict]:
    anchors = [w for w in words if DATE_RE.match(w[4]) and w[0] < 70 and w[1] > header_yc + 5]
    records = []
    for a in sorted(anchors, key=lambda w: w[1]):
        yc_a = _yc(a)
        weekday = ""
        for w in words:
            if w[0] < 45 and abs(_yc(w) - yc_a) < 5 and WEEKDAY_RE.match(w[4]):
                weekday = w[4]
                break

        limite_esquerdo = faixas[0][1]
        cells: dict[str, list[str]] = {}
        for w in words:
            if w is a or w[0] < limite_esquerdo or abs(_yc(w) - yc_a) >= 4:
                continue
            col = _col_for(_xc(w), faixas)
            if col:
                cells.setdefault(col, []).append(w[4])

        slot_tokens = {slot: cells[slot][0] for slot in SLOT_NAMES if cells.get(slot)}
        motivo = clean_text(" ".join(cells.get("tratamento", [])))
        status = _classify_day(slot_tokens, motivo)

        worked_min = 0
        if status in (
            PointStatus.TRABALHADO,
            PointStatus.MARCACAO_IMPAR,
            PointStatus.FALTA_PARCIAL,
            PointStatus.ATESTADO_PARCIAL,
        ):
            worked_min = _worked_minutes_from_slots(slot_tokens)

        occurrence = next(
            (v for v in slot_tokens.values() if v in (WHOLE_DAY_FOLGA, WHOLE_DAY_FERIADO, FALTA_WORD)),
            "",
        )

        record = {slot: (slot_tokens.get(slot, "") if TIME_RE.match(slot_tokens.get(slot, "")) else "") for slot in SLOT_NAMES}
        record.update({
            "date": a[4],
            "weekday": weekday,
            "occurrence": occurrence,
            "reason": motivo,
            "worked_minutes": worked_min,
            # Não exposto por dia neste layout (só o total do mês no
            # RESUMO) — CK_DESC não é verificável aqui, ver checksums.
            "discounted_minutes": 0,
            "schedule": [],
            "status": status,
            "lost_weekly_rest": False,
        })
        records.append(record)
    return records


def _label_y(rw: list[tuple], text: str, *, next_word: str | None = None, exclude_next: str | None = None) -> float | None:
    """Acha a linha (y) de um rótulo, desambiguando quando o mesmo texto
    aparece em mais de uma linha do RESUMO (ex.: "DSR" sozinho, na linha
    Pagos/Desc., contra "DSR Normais", no bloco de valor único) — algo que
    não dava pra resolver só com faixas de y aqui, porque as duas linhas
    ficam quase na mesma altura (diferença de ~1pt), intercaladas, não
    empilhadas em blocos separados como no layout original."""
    for w in rw:
        if w[4] != text:
            continue
        seguinte = next(
            (x for x in rw if abs(x[1] - w[1]) < 1 and 0 < x[0] - w[2] < 6),
            None,
        )
        nxt = seguinte[4] if seguinte else None
        if next_word is not None and nxt != next_word:
            continue
        if exclude_next is not None and nxt == exclude_next:
            continue
        return w[1]
    return None


def _extract_resumo_fields(words: list[tuple]) -> dict:
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
    col_a_value = 133.0

    def value_at_y(label_y: float | None, target_x: float, y_tol: float = 2.0, max_dx: float = 30.0):
        if label_y is None:
            return None
        candidatos = [w for w in rw if abs(w[1] - label_y) < y_tol and CENT_RE.match(w[4])]
        if not candidatos:
            return "00:00"
        melhor = min(candidatos, key=lambda w: abs(w[0] - target_x))
        return melhor[4] if abs(melhor[0] - target_x) <= max_dx else "00:00"

    raw: dict[str, str] = {}
    if (v := value_at_y(_label_y(rw, "Horas", next_word="Normais"), col_a_value)) is not None:
        raw["normal_hours"] = v
    if (v := value_at_y(_label_y(rw, "DSR", next_word="Normais"), col_a_value)) is not None:
        raw["dsr_normal"] = v
    if (v := value_at_y(_label_y(rw, "Total", next_word="Semanal"), col_a_value)) is not None:
        raw["weekly_total"] = v
    if (v := value_at_y(_label_y(rw, "Adc", next_word="Noturno"), col_a_value)) is not None:
        raw["night_additional_total"] = v
    if (v := value_at_y(_label_y(rw, "Tot", next_word="Descontado"), col_a_value)) is not None:
        raw["discounted_total"] = v

    htrab_y = _label_y(rw, "H.", next_word="Trab.")
    if (v := value_at_y(htrab_y, pagos_x)) is not None:
        raw["worked_hours_paid"] = v
    dsr_row_y = _label_y(rw, "DSR", exclude_next="Normais")
    if (v := value_at_y(dsr_row_y, pagos_x)) is not None:
        raw["dsr_paid"] = v
    if (v := value_at_y(dsr_row_y, desc_x)) is not None:
        raw["dsr_discount"] = v
    atrasos_y = _label_y(rw, "Atrasos")
    if (v := value_at_y(atrasos_y, desc_x)) is not None:
        raw["delays"] = v
    faltas_y = _label_y(rw, "Faltas")
    if (v := value_at_y(faltas_y, pagos_x)) is not None:
        raw["absences_paid"] = v
    if (v := value_at_y(faltas_y, desc_x)) is not None:
        raw["absences_discounted"] = v
    saidas_y = _label_y(rw, "Saídas")
    if (v := value_at_y(saidas_y, desc_x)) is not None:
        raw["early_departures"] = v

    # "H.E. 050%" e "H.E. A 050%" (e variantes 070/100%) — duas linhas que o
    # schema atual não distingue; somadas na mesma faixa de hora extra.
    extra_pct_min = {"050%": 0, "070%": 0, "100%": 0}
    for pw in (w for w in rw if w[4] in extra_pct_min):
        valor = next((w[4] for w in rw if abs(w[1] - pw[1]) < 2 and CENT_RE.match(w[4])), None)
        if valor:
            extra_pct_min[pw[4]] += to_minutes_cent(valor)

    for key, v in raw.items():
        fields[key] = minutes_to_time(to_minutes_cent(v))
    fields["overtime_50"] = minutes_to_time(extra_pct_min["050%"])
    fields["overtime_70"] = minutes_to_time(extra_pct_min["070%"])
    fields["overtime_100"] = minutes_to_time(extra_pct_min["100%"])

    return fields


def parse_employee_page_rep(page_text: str, words: list[tuple]) -> dict:
    import uuid

    lines = page_text.split("\n")

    name = extract_labeled_field(lines, ["Funcionário", "Funcionario"])
    cpf_raw = extract_labeled_field(lines, ["CPF"])
    role = extract_labeled_field(lines, ["Cargo"])
    admission = extract_labeled_field(lines, ["Admissão", "Admissao"])
    sector_raw = extract_labeled_field(lines, ["Setor"])

    sector_code, _, sector_description = sector_raw.partition(" ")
    if not sector_description:
        sector_description, sector_code = sector_code, ""

    matricula = next((w[4] for w in words if MATRICULA_RE.match(w[4]) and w[1] < 100), "")
    cpf = re.sub(r"\D", "", cpf_raw)

    # "Empresa"/CNPJ e "Per. de Ref." vêm em linhas separadas na extração
    # de texto corrido (a ordem de leitura do PDF não é "rótulo valor" numa
    # linha só aqui) — procurados pelo índice da linha, não por regex de
    # rótulo+valor numa linha.
    company_name = ""
    company_cnpj = ""
    idx_empresa = next((i for i, l in enumerate(lines) if clean_text(l) == "Empresa"), None)
    if idx_empresa is not None:
        if idx_empresa + 1 < len(lines):
            company_name = clean_text(lines[idx_empresa + 1])
        for l in lines[max(0, idx_empresa - 3): idx_empresa + 3]:
            m = CNPJ_RE.search(l)
            if m:
                company_cnpj = re.sub(r"\D", "", m.group())
                break

    period_start = period_end = ""
    idx_periodo = next((i for i, l in enumerate(lines) if clean_text(l).startswith("Per. de Ref")), None)
    if idx_periodo is not None:
        datas = []
        for l in lines[idx_periodo: idx_periodo + 6]:
            m = re.search(r"\d{2}/\d{2}/\d{4}", l)
            if m:
                datas.append(m.group())
        if len(datas) >= 2:
            period_start, period_end = datas[0], datas[1]

    if not name and not cpf:
        return {"name": "", "cpf": ""}

    header_yc = _find_header_yc(words)
    faixas = _calibrate_columns(words, header_yc)
    records = _parse_day_rows(words, faixas, header_yc)
    summary = _extract_resumo_fields(words)

    worked_minutes_total = sum(r["worked_minutes"] for r in records)

    worked_days = sum(1 for r in records if r["status"] == PointStatus.TRABALHADO)
    days_off = sum(1 for r in records if r["status"] in (PointStatus.DOMINGO, PointStatus.SABADO))
    vacation_days = sum(1 for r in records if r["status"] == PointStatus.FERIAS)
    medical_days = sum(1 for r in records if r["status"] in (PointStatus.ATESTADO_INTEGRAL, PointStatus.ATESTADO_PARCIAL))
    absence_days = sum(1 for r in records if r["status"] in (PointStatus.FALTA_INTEGRAL, PointStatus.FALTA_PARCIAL))
    inconsistencies = sum(1 for r in records if r["status"] == PointStatus.MARCACAO_IMPAR)

    summary.update({
        "worked_days": worked_days,
        "days_off": days_off,
        "vacation_days": vacation_days,
        "absence_days": absence_days,
        "medical_days": medical_days,
        "inconsistencies": inconsistencies,
    })

    checksums = {
        "ck_trab": to_minutes(summary["worked_hours_paid"]) == worked_minutes_total,
        # Não há coluna de horas descontadas por dia neste layout (só o
        # total mensal) — não dá pra conferir dia a dia. Sempre True aqui
        # não significa "conferido", ver nota de limitação no PR.
        "ck_desc": True,
    }

    return {
        "id": str(uuid.uuid4()),
        "matricula": matricula,
        "name": name,
        "cpf": cpf,
        "role": role,
        "sector_code": sector_code,
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
