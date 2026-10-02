from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class PointStatus(str, Enum):
    """Classificação do dia — ver §2.4 de reestruturacao-processar-ponto.md.
    Baseada em horas_trab/horas_desc e nos códigos de ocorrência (DOM, SAB,
    FERD, MEDIC, FALTA), nunca na contagem de tokens."""
    TRABALHADO = "TRABALHADO"
    DOMINGO = "DOMINGO"
    SABADO = "SABADO"
    FERIADO = "FERIADO"
    ATESTADO_INTEGRAL = "ATESTADO_INTEGRAL"
    ATESTADO_PARCIAL = "ATESTADO_PARCIAL"
    FALTA_INTEGRAL = "FALTA_INTEGRAL"
    FALTA_PARCIAL = "FALTA_PARCIAL"
    MARCACAO_IMPAR = "MARCACAO_IMPAR"

class PointRecord(BaseModel):
    date: str
    weekday: str
    extra_before_entry: str = ""
    extra_before_exit: str = ""
    first_period_entry: str = ""
    first_period_exit: str = ""
    second_period_entry: str = ""
    second_period_exit: str = ""
    extra_after_entry: str = ""
    extra_after_exit: str = ""
    occurrence: str = ""
    reason: str = ""
    worked_minutes: int = 0
    discounted_minutes: int = 0
    schedule: List[str] = []
    status: PointStatus
    # DSR perdido: domingo/sábado com horas_desc > 0 (ver AL_DSR_PERDIDO).
    lost_weekly_rest: bool = False

class EmployeeSummary(BaseModel):
    worked_days: int = 0
    days_off: int = 0
    vacation_days: int = 0
    absence_days: int = 0
    medical_days: int = 0
    inconsistencies: int = 0
    night_additional_total: str = "00:00"
    normal_hours: str = "00:00"
    dsr_normal: str = "00:00"
    weekly_total: str = "00:00"
    saldo_banco: str = "00:00"
    discounted_total: str = "00:00"
    worked_hours_paid: str = "00:00"
    dsr_paid: str = "00:00"
    dsr_discount: str = "00:00"
    delays: str = "00:00"
    absences_paid: str = "00:00"
    absences_discounted: str = "00:00"
    early_departures: str = "00:00"
    overtime_50: str = "00:00"
    overtime_70: str = "00:00"
    overtime_100: str = "00:00"

class Checksums(BaseModel):
    """Conferências internas — se alguma falhar, o colaborador deveria ser
    tratado como ERRO_LEITURA (ver §6.1 da reestruturação). Por ora só
    calculadas e expostas; o bloqueio de envio é de uma fase posterior."""
    ck_trab: bool = True
    ck_desc: bool = True

class Employee(BaseModel):
    id: str
    matricula: str = ""
    name: str
    cpf: str
    role: str
    sector_code: str = ""
    sector_description: str = ""
    schedule_label: str = ""
    admission: str = ""
    records: List[PointRecord] = []
    summary: EmployeeSummary = Field(default_factory=EmployeeSummary)
    checksums: Checksums = Field(default_factory=Checksums)

class UploadResult(BaseModel):
    upload_id: str
    file_name: str
    total_employees: int
    company_name: str = ""
    company_cnpj: str = ""
    period_start: str = ""
    period_end: str = ""
    employees: List[Employee]
