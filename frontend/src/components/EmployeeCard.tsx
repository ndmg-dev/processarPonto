import type { Employee } from '../types/point';
import { Link } from 'react-router-dom';

type EmployeeCardProps = {
  employee: Employee;
  uploadId: string;
};

export function EmployeeCard({ employee, uploadId }: EmployeeCardProps) {
  const { inconsistencies } = employee.summary;

  return (
    <Link to={`/result/${uploadId}/employee/${employee.id}`} className="block">
      <div className={`bg-card rounded-xl p-5 shadow-sm border-l-4 border-y border-r border-border hover:border-borderStrong transition-all cursor-pointer ${inconsistencies > 0 ? 'border-l-warning' : 'border-l-success'}`}>
        <h3 className="text-lg font-bold text-textPrimary mb-3 truncate" title={employee.name}>{employee.name}</h3>

        <div className="flex flex-col gap-2 text-sm text-textSecondary">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-textPrimary">CPF:</span> {employee.cpf}
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-textPrimary">Cargo:</span> <span className="truncate" title={employee.role}>{employee.role}</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-border flex justify-between items-center">
          <span className="text-sm text-textSecondary font-medium">{employee.records.length} registros</span>
          {inconsistencies > 0 ? (
            <span className="px-3 py-1 bg-warning/10 text-warning text-xs font-bold rounded-full">
              {inconsistencies} alertas
            </span>
          ) : (
            <span className="px-3 py-1 bg-success/10 text-success text-xs font-bold rounded-full">
              OK
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
