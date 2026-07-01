import re
from app.services.classifier import classify_record
from app.models.schemas import PointStatus

CPF_REGEX = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
TIME_REGEX = r"\b\d{2}:\d{2}\b"
DATE_LINE_REGEX = r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)\s+(\d{2}/\d{2})"
EMPLOYEE_REGEX = r"(?:Funcionário|Funcionario)\s*:\s*(\d*)\s*(.+)"
ROLE_REGEX = r"Cargo\s*:\s*(.+)"
SCHEDULE_MAP_REGEX = r"(\d{4})\s+((?:\d{2}:\d{2}\s*)+)"

def parse_schedule_map(text: str) -> dict:
    schedule_map = {}
    lines = text.split("\n")
    for line in lines:
        cleaned = clean_text(line)
        # Skip daily record lines starting with weekday and date
        if re.search(r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)\s+\d{2}/\d{2}", cleaned):
            continue
        matches = re.findall(SCHEDULE_MAP_REGEX, cleaned)
        for code, times_str in matches:
            times = re.findall(TIME_REGEX, times_str)
            schedule_map[code] = times
    return schedule_map

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def time_to_minutes(t: str) -> int:
    try:
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def align_times(actual_times: list[str], schedule_times: list[str]) -> list[str]:
    if not schedule_times:
        return (actual_times + ["", "", "", ""])[:4]
    
    slots = ["", "", "", ""]
    sch_len = len(schedule_times)
    sch_minutes = [time_to_minutes(t) for t in schedule_times]
    
    for act in actual_times:
        act_min = time_to_minutes(act)
        closest_idx = min(range(sch_len), key=lambda i: abs(sch_minutes[i] - act_min))
        if sch_len == 2:
            slots[closest_idx] = act
        else:
            if closest_idx < 4:
                slots[closest_idx] = act
            
    return slots

def parse_employee_page(page_text: str) -> dict:
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
            "extra_hours_50": "00:00",
            "extra_hours_100": "00:00",
            "delay_hours": "00:00",
            "absence_hours": "00:00",
            "early_exit_hours": "00:00"
        }
    }
    
    schedule_map = parse_schedule_map(page_text)
    
    for line in lines:
        cleaned_line = clean_text(line)
        
        # Parse Funcionario
        emp_match = re.search(EMPLOYEE_REGEX, cleaned_line, re.IGNORECASE)
        if emp_match:
            name_text = emp_match.group(2).strip()
            # Truncate at common layout separators on same line
            for sep in [" PIS", " CPF", " Cód", " Cargo", " Admissão", " Setor"]:
                if sep in name_text:
                    name_text = name_text.split(sep)[0]
            employee["name"] = name_text.strip()
            
            # Find ID if present (digits in group 1)
            emp_id = emp_match.group(1).strip()
            if emp_id:
                employee["id"] = emp_id
            
        # Parse CPF
        cpf_match = re.search(CPF_REGEX, cleaned_line)
        if cpf_match and not employee["cpf"]:
            employee["cpf"] = cpf_match.group(0)
            
        # Parse Role
        role_match = re.search(ROLE_REGEX, cleaned_line, re.IGNORECASE)
        if role_match and not employee["role"]:
            role_text = role_match.group(1).strip()
            for sep in [" Per. de Ref.", " Admissão", " Emissão"]:
                if sep in role_text:
                    role_text = role_text.split(sep)[0]
            employee["role"] = role_text.strip()
            
        # Parse Date Lines
        date_match = re.search(DATE_LINE_REGEX, cleaned_line)
        if date_match:
            weekday = date_match.group(1)
            date_str = date_match.group(2)
            
            # Find all times in the entire line first to clean line for code/occ extraction
            all_times = re.findall(TIME_REGEX, cleaned_line)
            
            # Clean times out to extract code/occurrence/reason
            rest_of_line = cleaned_line
            for t in all_times:
                rest_of_line = rest_of_line.replace(t, "", 1)
            
            # Try to find a schedule code (4 digits)
            schedule_code = ""
            code_match = re.search(r"\b(\d{4})\b", rest_of_line)
            if code_match:
                schedule_code = code_match.group(1)
                
            # Extract actual worked times from right_part if schedule code is present
            actual_times = []
            if schedule_code:
                parts = cleaned_line.split(" " + schedule_code + " ")
                right_part = parts[1] if len(parts) > 1 else ""
                actual_times = re.findall(TIME_REGEX, right_part)
            else:
                actual_times = all_times
                
            # Align times to slots
            first_entry, first_exit, second_entry, second_exit = "", "", "", ""
            aligned_times = align_times(actual_times, schedule_map.get(schedule_code, []))
            first_entry = aligned_times[0]
            first_exit = aligned_times[1]
            second_entry = aligned_times[2]
            second_exit = aligned_times[3]
            
            occurrence = ""
            occ_match = re.search(r"\b([A-Z])\b", rest_of_line)
            if occ_match:
                occurrence = occ_match.group(1)
                
            reason = re.sub(r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)\s+\d{2}/\d{2}", "", rest_of_line)
            reason = re.sub(r"\b\d{4}\b", "", reason)
            reason = re.sub(r"\b[A-Z]\b", "", reason)
            reason = clean_text(reason)
            
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
                "raw_line": cleaned_line
            }
            
            classified = classify_record(record, schedule_map)
            
            # Clear times for non-working statuses
            non_working_statuses = [
                PointStatus.FOLGA,
                PointStatus.DOMINGO,
                PointStatus.FERIAS,
                PointStatus.ATESTADO,
                PointStatus.FALTA_JUSTIFICADA,
                PointStatus.FALTA
            ]
            if classified["status"] in non_working_statuses:
                classified["first_period_entry"] = ""
                classified["first_period_exit"] = ""
                classified["second_period_entry"] = ""
                classified["second_period_exit"] = ""
                
            employee["records"].append(classified)
            
            # Update summary
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
                
    # If name/role are empty or ID is missing, try a page-wide search as fallback
    if not employee["id"]:
        # Find any 10-digit number like 0000000009
        id_match = re.search(r"\b(\d{10})\b", page_text)
        if id_match:
            employee["id"] = id_match.group(1)
        else:
            # Fallback to any digits near set or admission
            id_match = re.search(r"(?:Admissão|Setor)\s*:\s*\d{2}/\d{2}/\d{4}\s+(\d+)", page_text, re.IGNORECASE)
            if id_match:
                employee["id"] = id_match.group(1)
            else:
                # Use a clean fallback ID
                employee["id"] = employee["cpf"].replace(".", "").replace("-", "") if employee["cpf"] else "unknown"

    # Extract Summary hours metrics from the page text
    normalized_text = re.sub(r"\s+", " ", page_text)
    he_50_match = re.search(r"H\.E\.\s*050%\s*:\s*(\d{2,3}:\d{2})", normalized_text)
    he_100_match = re.search(r"H\.E\.\s*100%\s*:\s*(\d{2,3}:\d{2})", normalized_text)
    atrasos_match = re.search(r"Atrasos\s*(\d{2,3}:\d{2})", normalized_text)
    faltas_match = re.search(r"Faltas\s*(\d{2,3}:\d{2})", normalized_text)
    saidas_match = re.search(r"Saídas\s+Antecipada\s*(\d{2,3}:\d{2})", normalized_text)
    
    if he_50_match:
        employee["summary"]["extra_hours_50"] = he_50_match.group(1)
    if he_100_match:
        employee["summary"]["extra_hours_100"] = he_100_match.group(1)
    if atrasos_match:
        employee["summary"]["delay_hours"] = atrasos_match.group(1)
    if faltas_match:
        employee["summary"]["absence_hours"] = faltas_match.group(1)
    if saidas_match:
        employee["summary"]["early_exit_hours"] = saidas_match.group(1)
                
    return employee

def parse_pdf_pages(pages: list[str]) -> list[dict]:
    employees = []
    for page in pages:
        if not page.strip():
            continue
        emp_data = parse_employee_page(page)
        if emp_data["id"] or emp_data["name"]:
            employees.append(emp_data)
    return employees
