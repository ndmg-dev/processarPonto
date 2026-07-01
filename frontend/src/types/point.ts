export type PointStatus =
  | "TRABALHADO"
  | "TRABALHADO_COM_OCORRENCIA"
  | "TRABALHADO_PARCIAL"
  | "FOLGA"
  | "DOMINGO"
  | "FERIAS"
  | "ATESTADO"
  | "FALTA_JUSTIFICADA"
  | "FALTA"
  | "SERVICO_EXTERNO"
  | "INCONSISTENCIA";

export type PointRecord = {
  date: string;
  weekday: string;
  first_period_entry: string;
  first_period_exit: string;
  second_period_entry: string;
  second_period_exit: string;
  occurrence: string;
  reason: string;
  status: PointStatus;
  requires_second_period: boolean;
  has_missing_required_mark: boolean;
};

export type EmployeeSummary = {
  worked_days: number;
  days_off: number;
  vacation_days: number;
  absence_days: number;
  medical_days: number;
  inconsistencies: number;
  extra_hours_50: string;
  extra_hours_100: string;
  delay_hours: string;
  absence_hours: string;
  early_exit_hours: string;
};

export type Employee = {
  id: string;
  name: string;
  cpf: string;
  role: string;
  records: PointRecord[];
  summary: EmployeeSummary;
};

export type UploadResult = {
  upload_id: string;
  file_name: string;
  total_employees: number;
  employees: Employee[];
};
