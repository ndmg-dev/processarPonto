from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PointStatus(str, Enum):
    TRABALHADO = "TRABALHADO"
    TRABALHADO_COM_OCORRENCIA = "TRABALHADO_COM_OCORRENCIA"
    TRABALHADO_PARCIAL = "TRABALHADO_PARCIAL"
    FOLGA = "FOLGA"
    DOMINGO = "DOMINGO"
    FERIAS = "FERIAS"
    ATESTADO = "ATESTADO"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"
    FALTA = "FALTA"
    SERVICO_EXTERNO = "SERVICO_EXTERNO"
    INCONSISTENCIA = "INCONSISTENCIA"

class PointRecord(BaseModel):
    date: str
    weekday: str
    first_period_entry: str = ""
    first_period_exit: str = ""
    second_period_entry: str = ""
    second_period_exit: str = ""
    occurrence: str = ""
    reason: str = ""
    status: PointStatus
    requires_second_period: bool = True
    has_missing_required_mark: bool = False
    raw_line: Optional[str] = None

class EmployeeSummary(BaseModel):
    worked_days: int = 0
    days_off: int = 0
    vacation_days: int = 0
    absence_days: int = 0
    medical_days: int = 0
    inconsistencies: int = 0

class Employee(BaseModel):
    id: str
    name: str
    cpf: str
    role: str
    records: List[PointRecord] = []
    summary: EmployeeSummary = Field(default_factory=EmployeeSummary)

class UploadResult(BaseModel):
    upload_id: str
    file_name: str
    total_employees: int
    employees: List[Employee]
