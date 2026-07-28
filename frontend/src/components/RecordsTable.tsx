import type { PointRecord } from '../types/point';

type RecordsTableProps = {
  records: PointRecord[];
};

export function RecordsTable({ records }: RecordsTableProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'INCONSISTENCIA':
        return 'bg-warning/10 text-warning border-warning/30';
      case 'FALTA':
        return 'bg-error/10 text-error border-error/30';
      case 'TRABALHADO':
      case 'TRABALHADO_PARCIAL':
        return 'bg-success/10 text-success border-success/30';
      case 'TRABALHADO_COM_OCORRENCIA':
        return 'bg-goldDim text-primary border-gold/30';
      default:
        return 'bg-hover text-textSecondary border-border';
    }
  };

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ');
  };

  return (
    <div className="overflow-x-auto bg-card rounded-xl shadow-sm border border-border">
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-textSecondary uppercase bg-surface border-b border-border">
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
            <tr key={idx} className="border-b border-border hover:bg-hover transition-colors">
              <td className="px-4 py-3 font-medium text-textPrimary whitespace-nowrap">
                {record.weekday} {record.date}
              </td>
              <td className="px-4 py-3 text-center font-mono text-textSecondary">{record.first_period_entry || '-'}</td>
              <td className="px-4 py-3 text-center font-mono text-textSecondary">{record.first_period_exit || '-'}</td>
              <td className="px-4 py-3 text-center font-mono text-textSecondary">{record.second_period_entry || '-'}</td>
              <td className="px-4 py-3 text-center font-mono text-textSecondary">{record.second_period_exit || '-'}</td>
              <td className="px-4 py-3 text-center text-textSecondary">{record.occurrence || '-'}</td>
              <td className="px-4 py-3 text-textSecondary max-w-xs truncate" title={record.reason}>
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
