export type PointStatus =
  | "TRABALHADO"
  | "DOMINGO"
  | "SABADO"
  | "FERIADO"
  | "ATESTADO_INTEGRAL"
  | "ATESTADO_PARCIAL"
  | "FALTA_INTEGRAL"
  | "FALTA_PARCIAL"
  | "MARCACAO_IMPAR";

export type PointRecord = {
  date: string;
  weekday: string;
  extra_before_entry: string;
  extra_before_exit: string;
  first_period_entry: string;
  first_period_exit: string;
  second_period_entry: string;
  second_period_exit: string;
  extra_after_entry: string;
  extra_after_exit: string;
  occurrence: string;
  reason: string;
  worked_minutes: number;
  discounted_minutes: number;
  schedule: string[];
  status: PointStatus;
  lost_weekly_rest: boolean;
};

export type EmployeeSummary = {
  worked_days: number;
  days_off: number;
  vacation_days: number;
  absence_days: number;
  medical_days: number;
  inconsistencies: number;
  night_additional_total: string;
  normal_hours: string;
  dsr_normal: string;
  weekly_total: string;
  saldo_banco: string;
  discounted_total: string;
  worked_hours_paid: string;
  dsr_paid: string;
  dsr_discount: string;
  delays: string;
  absences_paid: string;
  absences_discounted: string;
  early_departures: string;
  overtime_50: string;
  overtime_70: string;
  overtime_100: string;
};

export type Checksums = {
  ck_trab: boolean;
  ck_desc: boolean;
};

export type Employee = {
  id: string;
  matricula: string;
  name: string;
  cpf: string;
  role: string;
  sector_code: string;
  sector_description: string;
  schedule_label: string;
  admission: string;
  records: PointRecord[];
  summary: EmployeeSummary;
  checksums: Checksums;
};

export type UploadResult = {
  upload_id: string;
  file_name: string;
  total_employees: number;
  company_name: string;
  company_cnpj: string;
  period_start: string;
  period_end: string;
  employees: Employee[];
};
