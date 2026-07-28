import { Users, FileText, AlertTriangle, Calendar, CheckCircle, Clock, Moon } from 'lucide-react';

type SummaryCardsProps = {
  totalEmployees: number;
  totalRecords: number;
  absences: number;
  vacations: number;
  daysOff: number;
  inconsistencies: number;
  nightAdditionalTotal: string;
};

export function SummaryCards({ totalEmployees, totalRecords, absences, vacations, daysOff, inconsistencies, nightAdditionalTotal }: SummaryCardsProps) {
  const cards = [
    { title: 'Colaboradores', value: totalEmployees, icon: Users, color: 'text-info', bg: 'bg-info/10' },
    { title: 'Registros Lidos', value: totalRecords, icon: FileText, color: 'text-primary', bg: 'bg-goldDim' },
    { title: 'Faltas', value: absences, icon: AlertTriangle, color: 'text-error', bg: 'bg-error/10' },
    { title: 'Férias', value: vacations, icon: Calendar, color: 'text-info', bg: 'bg-info/10' },
    { title: 'Folgas/DSR', value: daysOff, icon: CheckCircle, color: 'text-success', bg: 'bg-success/10' },
    { title: 'Inconsistências', value: inconsistencies, icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
    { title: 'Adicional Noturno', value: nightAdditionalTotal, icon: Moon, color: 'text-textSecondary', bg: 'bg-hover' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-4">
      {cards.map((card, idx) => (
        <div key={idx} className="bg-card rounded-xl p-4 shadow-sm border border-border flex flex-col items-center justify-center text-center hover:border-borderStrong transition-colors">
          <div className={`p-3 rounded-full ${card.bg} ${card.color} mb-3`}>
            <card.icon size={24} />
          </div>
          <p className="text-sm text-textSecondary font-medium mb-1">{card.title}</p>
          <p className="text-2xl font-bold text-textPrimary">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
