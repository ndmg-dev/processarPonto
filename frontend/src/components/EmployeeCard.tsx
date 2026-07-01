import type { Employee } from '../types/point';
import { Link } from 'react-router-dom';
import { AlertCircle, CheckCircle, ChevronRight } from 'lucide-react';

type EmployeeCardProps = {
  employee: Employee;
  uploadId: string;
};

export function EmployeeCard({ employee, uploadId }: EmployeeCardProps) {
  const { inconsistencies } = employee.summary;
  const hasInconsistencies = inconsistencies > 0;

  return (
    <Link to={`/result/${uploadId}/employee/${employee.id}`} className="block group">
      <div className={`bg-card rounded-xl p-5 border transition-all duration-300 relative overflow-hidden ${
        hasInconsistencies 
          ? 'border-warning/30 hover:border-warning/60 hover:shadow-[0_0_15px_rgba(245,158,11,0.05)]' 
          : 'border-zinc-800/80 hover:border-primary/40 hover:shadow-[0_0_15px_rgba(223,186,115,0.05)]'
      }`}>
        {/* Top/Side Decorative Accent Line */}
        <div className={`absolute top-0 left-0 bottom-0 w-[4px] ${hasInconsistencies ? 'bg-warning' : 'bg-primary'}`} />

        <div className="pl-2">
          {/* Header section */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <h3 className="text-base font-bold text-white truncate font-display group-hover:text-primary transition-colors" title={employee.name}>
              {employee.name}
            </h3>
            <ChevronRight size={16} className="text-textSecondary shrink-0 group-hover:text-white transition-all group-hover:translate-x-0.5" />
          </div>
          
          {/* CPF and Role info */}
          <div className="flex flex-col gap-1.5 text-xs text-textSecondary mb-4">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-zinc-500">CPF:</span> 
              <span className="font-mono text-zinc-300">{employee.cpf}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-zinc-500">Cargo:</span> 
              <span className="truncate text-zinc-300" title={employee.role}>{employee.role}</span>
            </div>
          </div>

          {/* Key Hours Metrics Grid directly on card */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 bg-zinc-950/45 p-3 rounded-lg border border-zinc-900/60 font-mono text-xs mb-4">
            <div className="flex flex-col">
              <span className="text-[9px] text-zinc-500 font-sans uppercase font-bold tracking-wider mb-0.5">H.E. 50%</span>
              <span className={`font-bold ${employee.summary.extra_hours_50 !== '00:00' ? 'text-primary' : 'text-zinc-500'}`}>
                {employee.summary.extra_hours_50}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-zinc-500 font-sans uppercase font-bold tracking-wider mb-0.5">H.E. 100%</span>
              <span className={`font-bold ${employee.summary.extra_hours_100 !== '00:00' ? 'text-primary' : 'text-zinc-500'}`}>
                {employee.summary.extra_hours_100}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-zinc-500 font-sans uppercase font-bold tracking-wider mb-0.5">Atrasos</span>
              <span className={`font-bold ${employee.summary.delay_hours !== '00:00' ? 'text-warning' : 'text-zinc-500'}`}>
                {employee.summary.delay_hours}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[9px] text-zinc-500 font-sans uppercase font-bold tracking-wider mb-0.5">Faltas</span>
              <span className={`font-bold ${employee.summary.absence_hours !== '00:00' ? 'text-error' : 'text-zinc-500'}`}>
                {employee.summary.absence_hours}
              </span>
            </div>
          </div>

          {/* Footer stats section */}
          <div className="pt-4 border-t border-zinc-800/60 flex justify-between items-center text-xs">
            <span className="text-zinc-500 font-medium font-mono">{employee.records.length} registros</span>
            {hasInconsistencies ? (
              <span className="px-2.5 py-1 bg-warning/10 text-warning text-[10px] tracking-wider font-extrabold uppercase rounded-md border border-warning/15 flex items-center gap-1">
                <AlertCircle size={10} />
                {inconsistencies} alertas
              </span>
            ) : (
              <span className="px-2.5 py-1 bg-success/10 text-success text-[10px] tracking-wider font-extrabold uppercase rounded-md border border-success/15 flex items-center gap-1">
                <CheckCircle size={10} />
                Regular
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
