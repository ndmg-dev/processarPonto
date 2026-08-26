import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUploadResult } from '../api/client';
import type { Employee } from '../types/point';
import { RecordsTable } from '../components/RecordsTable';
import { ArrowLeft, IdCard, Briefcase } from 'lucide-react';

export function EmployeeDetailPage() {
  const { uploadId, employeeId } = useParams<{ uploadId: string, employeeId: string }>();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (uploadId && employeeId) {
      getUploadResult(uploadId)
        .then(data => {
          const emp = data.employees.find(e => e.id === employeeId);
          setEmployee(emp || null);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [uploadId, employeeId]);

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div></div>;
  }

  if (!employee) {
    return <div className="text-center mt-20 text-error font-bold text-xl">Colaborador não encontrado.</div>;
  }

  const { summary } = employee;

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/result/${uploadId}`} className="flex items-center gap-2 text-secondary hover:underline mb-4">
          <ArrowLeft size={20} /> Voltar para o resumo
        </Link>
      </div>

      <div className="bg-card rounded-2xl shadow-sm border border-border p-8">
        <div className="flex flex-col md:flex-row md:items-center gap-6 justify-between">
          <div>
            <h2 className="text-3xl font-bold text-textPrimary mb-2">{employee.name}</h2>
            <div className="flex flex-wrap gap-4 text-textSecondary">
              <div className="flex items-center gap-1.5">
                <IdCard size={18} />
                <span>CPF: {employee.cpf}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Briefcase size={18} />
                <span>Cargo: {employee.role}</span>
              </div>
            </div>
          </div>

          <div className="flex gap-3 flex-wrap">
            <div className="bg-surface px-4 py-2 rounded-lg border border-border text-center">
              <p className="text-xs text-textSecondary uppercase font-bold">Registros</p>
              <p className="text-xl font-bold text-textPrimary">{employee.records.length}</p>
            </div>
            <div className="bg-success/10 px-4 py-2 rounded-lg border border-success/30 text-center">
              <p className="text-xs text-success uppercase font-bold">Trabalhados</p>
              <p className="text-xl font-bold text-success">{summary.worked_days}</p>
            </div>
            <div className="bg-warning/10 px-4 py-2 rounded-lg border border-warning/30 text-center">
              <p className="text-xs text-warning uppercase font-bold">Inconsistências</p>
              <p className="text-xl font-bold text-warning">{summary.inconsistencies}</p>
            </div>
            <div className="bg-goldDim px-4 py-2 rounded-lg border border-gold/30 text-center">
              <p className="text-xs text-primary uppercase font-bold">Adicional Noturno</p>
              <p className="text-xl font-bold text-primary">{summary.night_additional_total}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-2xl font-bold text-textPrimary mb-4">Resumo de Horas</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card rounded-2xl shadow-sm border border-border p-5 space-y-3">
            <SummaryRow label="Horas Normais" value={summary.normal_hours} />
            <SummaryRow label="DSR Normais" value={summary.dsr_normal} />
            <SummaryRow label="Total Semanal" value={summary.weekly_total} />
            <SummaryRow label="Adc Noturno" value={summary.night_additional_total} />
            <SummaryRow label="Tot Descontado" value={summary.discounted_total} />
          </div>

          <div className="bg-card rounded-2xl shadow-sm border border-border p-5 space-y-3">
            <div className="flex justify-between text-xs font-bold text-textSecondary uppercase pb-2 border-b border-border">
              <span></span>
              <div className="flex gap-6">
                <span>Pagos</span>
                <span>Desc.</span>
              </div>
            </div>
            <SummaryPairRow label="H. Trab." paid={summary.worked_hours_paid} />
            <SummaryPairRow label="DSR" paid={summary.dsr_paid} discount={summary.dsr_discount} />
            <SummaryPairRow label="Atrasos" discount={summary.delays} />
            <SummaryPairRow label="Faltas" discount={summary.absences_time} />
            <SummaryPairRow label="Saídas Antecipadas" discount={summary.early_departures} />
          </div>

          <div className="bg-card rounded-2xl shadow-sm border border-border p-5 space-y-3">
            <SummaryRow label="H.E. 050%" value={summary.overtime_50} />
            {summary.overtime_extra_label && (
              <SummaryRow label={summary.overtime_extra_label} value={summary.overtime_extra_value} />
            )}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-2xl font-bold text-textPrimary mb-4">Registros Diários</h3>
        <RecordsTable records={employee.records} />
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-textSecondary">{label}</span>
      <span className="text-sm font-bold text-textPrimary">{value}</span>
    </div>
  );
}

function SummaryPairRow({ label, paid, discount }: { label: string; paid?: string; discount?: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-textSecondary">{label}</span>
      <div className="flex gap-6">
        <span className="text-sm font-bold text-textPrimary w-12 text-right">{paid ?? '-'}</span>
        <span className="text-sm font-bold text-textPrimary w-12 text-right">{discount ?? '-'}</span>
      </div>
    </div>
  );
}
