import type { PointRecord } from '../types/point';
import { AlertCircle, CheckCircle, FileWarning, HelpCircle } from 'lucide-react';

type RecordsTableProps = {
  records: PointRecord[];
};

export function RecordsTable({ records }: RecordsTableProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'INCONSISTENCIA':
        return 'bg-warning/10 text-warning border-warning/20';
      case 'FALTA':
        return 'bg-error/10 text-error border-error/20';
      case 'TRABALHADO':
      case 'TRABALHADO_PARCIAL':
        return 'bg-success/10 text-success border-success/20';
      case 'TRABALHADO_COM_OCORRENCIA':
        return 'bg-primary/10 text-primary border-primary/20';
      default:
        return 'bg-zinc-800/40 text-textSecondary border-zinc-700/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'INCONSISTENCIA':
        return <FileWarning size={12} className="inline mr-1" />;
      case 'FALTA':
        return <AlertCircle size={12} className="inline mr-1" />;
      case 'TRABALHADO':
      case 'TRABALHADO_PARCIAL':
        return <CheckCircle size={12} className="inline mr-1" />;
      default:
        return <HelpCircle size={12} className="inline mr-1" />;
    }
  };

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ');
  };

  return (
    <div className="overflow-x-auto bg-card rounded-xl border border-zinc-850 shadow-premium">
      <table className="w-full text-xs text-left border-collapse">
        <thead>
          <tr className="border-b border-zinc-800/80 bg-zinc-950/80 text-[10px] tracking-widest text-textSecondary uppercase">
            <th className="px-5 py-4 font-bold">Data</th>
            <th className="px-4 py-4 text-center font-bold">Entrada 1</th>
            <th className="px-4 py-4 text-center font-bold">Saída 1</th>
            <th className="px-4 py-4 text-center font-bold">Entrada 2</th>
            <th className="px-4 py-4 text-center font-bold">Saída 2</th>
            <th className="px-4 py-4 text-center font-bold">Ocorrência</th>
            <th className="px-5 py-4 font-bold">Motivo / Justificativa</th>
            <th className="px-5 py-4 font-bold">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-900">
          {records.map((record, idx) => (
            <tr key={idx} className="hover:bg-zinc-900/45 transition-colors group">
              <td className="px-5 py-3.5 font-semibold text-white whitespace-nowrap">
                <span className="text-zinc-500 font-mono font-normal mr-2">
                  {record.weekday}
                </span>
                {record.date}
              </td>
              <td className="px-4 py-3.5 text-center font-mono text-zinc-300 bg-zinc-950/20 group-hover:text-primary transition-colors">
                {record.first_period_entry || '—'}
              </td>
              <td className="px-4 py-3.5 text-center font-mono text-zinc-300 bg-zinc-950/20 group-hover:text-primary transition-colors">
                {record.first_period_exit || '—'}
              </td>
              <td className="px-4 py-3.5 text-center font-mono text-zinc-300 bg-zinc-950/20 group-hover:text-primary transition-colors">
                {record.second_period_entry || '—'}
              </td>
              <td className="px-4 py-3.5 text-center font-mono text-zinc-300 bg-zinc-950/20 group-hover:text-primary transition-colors">
                {record.second_period_exit || '—'}
              </td>
              <td className="px-4 py-3.5 text-center font-mono font-medium text-primary">
                {record.occurrence || '—'}
              </td>
              <td className="px-5 py-3.5 text-textSecondary max-w-xs truncate" title={record.reason}>
                {record.reason || '—'}
              </td>
              <td className="px-5 py-3.5 whitespace-nowrap">
                <span className={`px-2.5 py-1 text-[10px] font-extrabold tracking-wider uppercase rounded border flex items-center w-fit ${getStatusColor(record.status)}`}>
                  {getStatusIcon(record.status)}
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
