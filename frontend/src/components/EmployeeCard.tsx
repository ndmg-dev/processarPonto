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
      <div className={`bg-white rounded-xl p-5 shadow-sm border-l-4 hover:shadow-md transition-all cursor-pointer ${inconsistencies > 0 ? 'border-orange-500' : 'border-green-500'}`}>
        <h3 className="text-lg font-bold text-gray-900 mb-3 truncate" title={employee.name}>{employee.name}</h3>
        
        <div className="flex flex-col gap-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span className="font-semibold">CPF:</span> {employee.cpf}
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold">Cargo:</span> <span className="truncate" title={employee.role}>{employee.role}</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
          <span className="text-sm text-gray-500 font-medium">{employee.records.length} registros</span>
          {inconsistencies > 0 ? (
            <span className="px-3 py-1 bg-orange-100 text-orange-700 text-xs font-bold rounded-full">
              {inconsistencies} alertas
            </span>
          ) : (
            <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
              OK
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
