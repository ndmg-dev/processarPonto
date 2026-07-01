import { Users, FileText, AlertTriangle, Calendar, CheckCircle, Clock } from 'lucide-react';

type SummaryCardsProps = {
  totalEmployees: number;
  totalRecords: number;
  absences: number;
  vacations: number;
  daysOff: number;
  inconsistencies: number;
};

export function SummaryCards({ totalEmployees, totalRecords, absences, vacations, daysOff, inconsistencies }: SummaryCardsProps) {
  const cards = [
    { 
      title: 'Colaboradores', 
      value: totalEmployees, 
      icon: Users, 
      color: 'text-primary', 
      bg: 'bg-primary/5 border-primary/20 shadow-[0_0_15px_rgba(223,186,115,0.02)]' 
    },
    { 
      title: 'Registros Lidos', 
      value: totalRecords, 
      icon: FileText, 
      color: 'text-slate-300', 
      bg: 'bg-slate-500/5 border-slate-700/30' 
    },
    { 
      title: 'Faltas', 
      value: absences, 
      icon: AlertTriangle, 
      color: absences > 0 ? 'text-error' : 'text-slate-400', 
      bg: absences > 0 ? 'bg-error/5 border-error/20' : 'bg-zinc-800/10 border-zinc-800/30' 
    },
    { 
      title: 'Férias', 
      value: vacations, 
      icon: Calendar, 
      color: 'text-indigo-400', 
      bg: 'bg-indigo-500/5 border-indigo-500/10' 
    },
    { 
      title: 'Folgas/DSR', 
      value: daysOff, 
      icon: CheckCircle, 
      color: 'text-success', 
      bg: 'bg-success/5 border-success/15' 
    },
    { 
      title: 'Inconsistências', 
      value: inconsistencies, 
      icon: Clock, 
      color: inconsistencies > 0 ? 'text-warning' : 'text-slate-400', 
      bg: inconsistencies > 0 ? 'bg-warning/5 border-warning/20' : 'bg-zinc-800/10 border-zinc-800/30' 
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => (
        <div 
          key={idx} 
          className={`bg-card rounded-xl p-5 border flex flex-col items-center justify-center text-center transition-all duration-300 hover:shadow-premium group ${card.bg}`}
        >
          <div className={`p-2.5 rounded-lg border border-current/10 bg-black/40 mb-3 transition-transform duration-300 group-hover:scale-110 ${card.color}`}>
            <card.icon size={20} />
          </div>
          <p className="text-xs text-textSecondary font-medium tracking-wide uppercase mb-1.5">{card.title}</p>
          <p className="text-2xl font-black font-display text-white tracking-tight">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
