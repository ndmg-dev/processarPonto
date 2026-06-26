import type { PointRecord } from '../types/point';

type RecordsTableProps = {
  records: PointRecord[];
};

export function RecordsTable({ records }: RecordsTableProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'INCONSISTENCIA':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'FALTA':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'TRABALHADO':
      case 'TRABALHADO_PARCIAL':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'TRABALHADO_COM_OCORRENCIA':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ');
  };

  return (
    <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3">Data</th>
            <th className="px-4 py-3 text-center">Entrada 1</th>
            <th className="px-4 py-3 text-center">Saída 1</th>
            <th className="px-4 py-3 text-center">Entrada 2</th>
            <th className="px-4 py-3 text-center">Saída 2</th>
            <th className="px-4 py-3 text-center">Oc.</th>
            <th className="px-4 py-3">Motivo</th>
            <th className="px-4 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record, idx) => (
            <tr key={idx} className="border-b hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">
                {record.weekday} {record.date}
              </td>
              <td className="px-4 py-3 text-center font-mono">{record.first_period_entry || '-'}</td>
              <td className="px-4 py-3 text-center font-mono">{record.first_period_exit || '-'}</td>
              <td className="px-4 py-3 text-center font-mono">{record.second_period_entry || '-'}</td>
              <td className="px-4 py-3 text-center font-mono">{record.second_period_exit || '-'}</td>
              <td className="px-4 py-3 text-center">{record.occurrence || '-'}</td>
              <td className="px-4 py-3 text-gray-600 max-w-xs truncate" title={record.reason}>
                {record.reason || '-'}
              </td>
              <td className="px-4 py-3">
                <span className={`px-2.5 py-1 text-xs font-semibold rounded-md border ${getStatusColor(record.status)}`}>
                  {formatStatus(record.status)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
