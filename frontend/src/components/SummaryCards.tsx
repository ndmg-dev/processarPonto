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
    { title: 'Colaboradores', value: totalEmployees, icon: Users, color: 'text-blue-600', bg: 'bg-blue-100' },
    { title: 'Registros Lidos', value: totalRecords, icon: FileText, color: 'text-indigo-600', bg: 'bg-indigo-100' },
    { title: 'Faltas', value: absences, icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100' },
    { title: 'Férias', value: vacations, icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-100' },
    { title: 'Folgas/DSR', value: daysOff, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100' },
    { title: 'Inconsistências', value: inconsistencies, icon: Clock, color: 'text-orange-600', bg: 'bg-orange-100' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => (
        <div key={idx} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow">
          <div className={`p-3 rounded-full ${card.bg} ${card.color} mb-3`}>
            <card.icon size={24} />
          </div>
          <p className="text-sm text-gray-500 font-medium mb-1">{card.title}</p>
          <p className="text-2xl font-bold text-gray-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
