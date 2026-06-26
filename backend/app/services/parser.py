import re
from app.services.classifier import classify_record
from app.models.schemas import PointStatus

CPF_REGEX = r"\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}"
TIME_REGEX = r"\\b\\d{2}:\\d{2}\\b"
DATE_LINE_REGEX = r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)\\s+(\\d{2}/\\d{2})"
EMPLOYEE_REGEX = r"(?:Funcionário|Funcionario)\\s*:\\s*(\\d+)\\s+-\\s+(.+)|(?:Funcionário|Funcionario)\\s*:\\s*(\\d+)\\s+(.+)"
ROLE_REGEX = r"Cargo\\s*:\\s*(.+)"
SCHEDULE_MAP_REGEX = r"(\\d{4})\\s+-\\s+((?:\\d{2}:\\d{2}\\s*)+)"

def parse_schedule_map(text: str) -> dict:
    schedule_map = {}
    lines = text.split("\\n")
    for line in lines:
        matches = re.findall(SCHEDULE_MAP_REGEX, line)
        for code, times_str in matches:
            times = re.findall(TIME_REGEX, times_str)
            schedule_map[code] = times
    return schedule_map

def clean_text(text: str) -> str:
    return re.sub(r"\\s+", " ", text).strip()

def parse_employee_page(page_text: str) -> dict:
    lines = page_text.split("\\n")
    
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
            "inconsistencies": 0
        }
    }
    
    schedule_map = parse_schedule_map(page_text)
    
    for line in lines:
        cleaned_line = clean_text(line)
        
        # Parse Funcionario
        emp_match = re.search(EMPLOYEE_REGEX, cleaned_line, re.IGNORECASE)
        if emp_match:
            groups = emp_match.groups()
            if groups[0]:
                employee["id"] = groups[0]
                employee["name"] = groups[1].strip()
            else:
                employee["id"] = groups[2]
                employee["name"] = groups[3].strip()
                
        # Parse CPF
        cpf_match = re.search(CPF_REGEX, cleaned_line)
        if cpf_match and not employee["cpf"]:
            employee["cpf"] = cpf_match.group(0)
            
        # Parse Role
        role_match = re.search(ROLE_REGEX, cleaned_line, re.IGNORECASE)
        if role_match and not employee["role"]:
            employee["role"] = role_match.group(1).strip()
            
        # Parse Date Lines
        date_match = re.search(DATE_LINE_REGEX, cleaned_line)
        if date_match:
            weekday = date_match.group(1)
            date_str = date_match.group(2)
            
            # Find all times in the line
            times = re.findall(TIME_REGEX, cleaned_line)
            
            # Remove times from line to extract occurrence/reason/code
            rest_of_line = cleaned_line
            for t in times:
                rest_of_line = rest_of_line.replace(t, "", 1)
            
            # Try to find a schedule code (4 digits)
            schedule_code = ""
            code_match = re.search(r"\\b(\\d{4})\\b", rest_of_line)
            if code_match:
                schedule_code = code_match.group(1)
                
            occurrence = ""
            # A single letter like I, M, etc usually isolated
            occ_match = re.search(r"\\b([A-Z])\\b", rest_of_line)
            if occ_match:
                occurrence = occ_match.group(1)
                
            # Reason is usually at the end
            # Try to grab everything after a certain point or just the rest
            # We'll just clean up the rest
            reason = re.sub(r"^(Seg|Ter|Qua|Qui|Sex|Sab|Sáb|Dom)\\s+\\d{2}/\\d{2}", "", rest_of_line)
            reason = re.sub(r"\\b\\d{4}\\b", "", reason)
            reason = re.sub(r"\\b[A-Z]\\b", "", reason)
            reason = clean_text(reason)
            
            # Distribute times
            first_entry, first_exit, second_entry, second_exit = "", "", "", ""
            if len(times) >= 1: first_entry = times[0]
            if len(times) >= 2: first_exit = times[1]
            if len(times) >= 3: second_entry = times[2]
            if len(times) >= 4: second_exit = times[3]
            
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
