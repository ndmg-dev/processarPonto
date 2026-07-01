import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUploadResult } from '../api/client';
import type { Employee, PointRecord } from '../types/point';
import { RecordsTable } from '../components/RecordsTable';
import {
  ArrowLeft, IdCard, Briefcase, AlertCircle, CalendarX, CalendarCheck,
  ShieldAlert, Clock, Timer, ChevronDown, ChevronUp, Info, Printer
} from 'lucide-react';

type OccurrenceGroup = {
  label: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  records: PointRecord[];
  description: string;
};

export function EmployeeDetailPage() {
  const { uploadId, employeeId } = useParams<{ uploadId: string, employeeId: string }>();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>('faltas');
  const [isPrinting, setIsPrinting] = useState(false);

  const handlePrint = () => {
    setIsPrinting(true);
    setTimeout(() => {
      window.print();
      setIsPrinting(false);
    }, 200);
  };

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

  const occurrenceGroups = useMemo<OccurrenceGroup[]>(() => {
    if (!employee) return [];

    const faltas = employee.records.filter(r => r.status === 'FALTA');
    const faltasJustificadas = employee.records.filter(r => r.status === 'FALTA_JUSTIFICADA');
    const atestados = employee.records.filter(r => r.status === 'ATESTADO');
    const ferias = employee.records.filter(r => r.status === 'FERIAS');
    const inconsistencias = employee.records.filter(r => r.status === 'INCONSISTENCIA');
    const ocorrencias = employee.records.filter(r => r.status === 'TRABALHADO_COM_OCORRENCIA');

    return [
      {
        label: 'Faltas Injustificadas',
        icon: <CalendarX size={16} />,
        color: 'text-error',
        bgColor: 'bg-error/8',
        borderColor: 'border-error/25',
        records: faltas,
        description: 'Dias em que o colaborador não compareceu ao trabalho sem justificativa registrada. Faltas injustificadas geram desconto no salário e podem acarretar perda do DSR (Descanso Semanal Remunerado) da semana correspondente.',
      },
      {
        label: 'Faltas Justificadas',
        icon: <ShieldAlert size={16} />,
        color: 'text-amber-400',
        bgColor: 'bg-amber-500/8',
        borderColor: 'border-amber-500/20',
        records: faltasJustificadas,
        description: 'Dias com falta abonada mediante justificativa legal (ex: falecimento, casamento, doação de sangue, etc.). Não geram desconto no salário nem perda de DSR.',
      },
      {
        label: 'Atestados Médicos',
        icon: <CalendarCheck size={16} />,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/8',
        borderColor: 'border-blue-500/20',
        records: atestados,
        description: 'Dias justificados por atestado médico. Até 15 dias consecutivos são de responsabilidade do empregador. A partir do 16º dia, o colaborador deve ser encaminhado ao INSS.',
      },
      {
        label: 'Férias',
        icon: <CalendarCheck size={16} />,
        color: 'text-indigo-400',
        bgColor: 'bg-indigo-500/8',
        borderColor: 'border-indigo-500/20',
        records: ferias,
        description: 'Dias de férias regulamentares gozadas pelo colaborador no período.',
      },
      {
        label: 'Inconsistências',
        icon: <AlertCircle size={16} />,
        color: 'text-warning',
        bgColor: 'bg-warning/8',
        borderColor: 'border-warning/20',
        records: inconsistencias,
        description: 'Registros com marcações incompletas ou irregulares (ex: faltando entrada ou saída). Esses dias precisam de tratamento manual pelo RH antes do fechamento da folha.',
      },
      {
        label: 'Trabalhado com Ocorrência',
        icon: <Clock size={16} />,
        color: 'text-primary',
        bgColor: 'bg-primary/8',
        borderColor: 'border-primary/20',
        records: ocorrencias,
        description: 'Dias trabalhados que possuem alguma ocorrência registrada (atraso, saída antecipada, hora extra, etc.). Verifique a coluna "Ocorrência" na tabela de registros para detalhes.',
      },
    ].filter(g => g.records.length > 0);
  }, [employee]);

  const toggleSection = (label: string) => {
    setExpandedSection(prev => prev === label ? null : label);
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-[50vh] gap-4">
        <div className="relative w-12 h-12">
          <div className="absolute inset-0 rounded-full border-2 border-zinc-800" />
          <div className="absolute inset-0 rounded-full border-2 border-t-primary border-r-primary animate-spin" />
        </div>
        <p className="text-sm text-textSecondary font-medium font-mono tracking-wider animate-pulse">Carregando registro do colaborador...</p>
      </div>
    );
  }

  if (!employee) {
    return (
      <div className="text-center py-20 animate-fadeIn">
        <div className="text-error text-xl font-bold mb-3">Colaborador não encontrado</div>
        <p className="text-textSecondary text-sm mb-6">O colaborador solicitado não existe neste espelho de ponto.</p>
        <Link to={`/result/${uploadId}`} className="inline-flex items-center gap-2 text-primary hover:underline">
          <ArrowLeft size={16} /> Voltar para o painel
        </Link>
      </div>
    );
  }

  const { summary } = employee;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Bar with actions */}
      <div className="no-print flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <Link to={`/result/${uploadId}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-textSecondary hover:text-white transition-colors group">
          <ArrowLeft size={14} className="transition-transform group-hover:-translate-x-0.5" /> Voltar para o resumo consolidado
        </Link>
        <button
          onClick={handlePrint}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gold-gradient text-background px-6 py-3 rounded-xl font-bold font-display text-xs tracking-wider uppercase transition-all duration-300 hover:bg-gold-gradient-hover active:scale-[0.98] shadow-md hover:shadow-lg select-none cursor-pointer"
        >
          <Printer size={16} />
          Imprimir Relatório
        </button>
      </div>

      {/* Header Info Card */}
      <div className="bg-card rounded-2xl shadow-premium border border-zinc-800/80 p-6 md:p-8 relative overflow-hidden">
        {/* Glow */}
        <div className="absolute top-0 right-0 w-40 h-40 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col gap-6 relative z-10">
          {/* Seção Superior: Nome do colaborador e dados (CPF/Cargo) */}
          <div className="border-b border-zinc-800/40 pb-5">
            <div className="overflow-x-auto scrollbar-none mb-3">
              <h2 className="text-2xl md:text-3xl font-bold font-display text-white whitespace-nowrap">
                {employee.name}
              </h2>
            </div>
            
            <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-textSecondary">
              <div className="flex items-center gap-2 bg-zinc-950/40 px-3 py-1.5 rounded-lg border border-zinc-900/60">
                <IdCard size={14} className="text-zinc-500" />
                <span>CPF: <span className="font-mono text-zinc-300 font-medium">{employee.cpf}</span></span>
              </div>
              <div className="flex items-center gap-2 bg-zinc-950/40 px-3 py-1.5 rounded-lg border border-zinc-900/60">
                <Briefcase size={14} className="text-zinc-500" />
                <span>Cargo: <span className="text-zinc-300 font-medium">{employee.role}</span></span>
              </div>
            </div>
          </div>
          
          {/* Seção Inferior: Grid de Estatísticas Rápidas (Largura Total) */}
          <div className="flex gap-3 flex-wrap">
            <div className="bg-zinc-950/60 px-4 py-3 rounded-xl border border-zinc-850 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-zinc-500 uppercase tracking-widest font-black mb-1">Registros</p>
              <p className="text-lg font-black font-mono text-white">{employee.records.length}</p>
            </div>
            
            <div className="bg-success/5 px-4 py-3 rounded-xl border border-success/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-success/70 uppercase tracking-widest font-black mb-1">Trabalhados (Dias)</p>
              <p className="text-lg font-black font-mono text-success">{summary.worked_days}</p>
            </div>

            <div className="bg-primary/5 px-4 py-3 rounded-xl border border-primary/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-primary/70 uppercase tracking-widest font-black mb-1">H.E. 50%</p>
              <p className={`text-lg font-black font-mono ${summary.extra_hours_50 !== '00:00' ? 'text-primary' : 'text-zinc-500'}`}>{summary.extra_hours_50}</p>
            </div>

            <div className="bg-primary/5 px-4 py-3 rounded-xl border border-primary/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-primary/70 uppercase tracking-widest font-black mb-1">H.E. 100%</p>
              <p className={`text-lg font-black font-mono ${summary.extra_hours_100 !== '00:00' ? 'text-primary' : 'text-zinc-500'}`}>{summary.extra_hours_100}</p>
            </div>

            <div className="bg-warning/5 px-4 py-3 rounded-xl border border-warning/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-warning/70 uppercase tracking-widest font-black mb-1">Atrasos</p>
              <p className={`text-lg font-black font-mono ${summary.delay_hours !== '00:00' ? 'text-warning' : 'text-zinc-500'}`}>{summary.delay_hours}</p>
            </div>

            <div className="bg-error/5 px-4 py-3 rounded-xl border border-error/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-error/70 uppercase tracking-widest font-black mb-1">Faltas (Horas)</p>
              <p className={`text-lg font-black font-mono ${summary.absence_hours !== '00:00' ? 'text-error' : 'text-zinc-500'}`}>{summary.absence_hours}</p>
            </div>

            <div className="bg-warning/5 px-4 py-3 rounded-xl border border-warning/15 text-center min-w-[90px] shadow-sm flex-1 sm:flex-initial">
              <p className="text-[9px] text-warning/70 uppercase tracking-widest font-black mb-1">Alertas (Dias)</p>
              <p className="text-lg font-black font-mono text-warning">{summary.inconsistencies}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* ABSENCES & OCCURRENCES ANALYSIS SECTION */}
      {/* ═══════════════════════════════════════════════════════════ */}
      {occurrenceGroups.length > 0 && (
        <div className="bg-card rounded-2xl shadow-premium border border-zinc-800/80 p-6 md:p-8">
          <div className="mb-6">
            <h3 className="text-lg font-bold font-display text-white flex items-center gap-2">
              <Info size={18} className="text-primary" />
              Análise de Faltas e Ocorrências
            </h3>
            <p className="text-xs text-textSecondary mt-1">
              Detalhamento de cada tipo de ausência e ocorrência registrada no período, com explicação do impacto.
            </p>
          </div>

          {/* Overview mini-cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
            <MiniStatCard
              label="Faltas"
              value={summary.absence_days}
              hours={summary.absence_hours}
              color={summary.absence_days > 0 ? 'error' : 'zinc'}
            />
            <MiniStatCard
              label="Atestados"
              value={summary.medical_days}
              color={summary.medical_days > 0 ? 'blue' : 'zinc'}
            />
            <MiniStatCard
              label="Férias"
              value={summary.vacation_days}
              color={summary.vacation_days > 0 ? 'indigo' : 'zinc'}
            />
            <MiniStatCard
              label="Folgas"
              value={summary.days_off}
              color={summary.days_off > 0 ? 'success' : 'zinc'}
            />
            <MiniStatCard
              label="Atrasos"
              hours={summary.delay_hours}
              color={summary.delay_hours !== '00:00' ? 'warning' : 'zinc'}
            />
            <MiniStatCard
              label="Inconsistências"
              value={summary.inconsistencies}
              color={summary.inconsistencies > 0 ? 'warning' : 'zinc'}
            />
          </div>

          {/* Accordion sections for each group */}
          <div className="space-y-3">
            {occurrenceGroups.map(group => {
              const isExpanded = isPrinting || expandedSection === group.label;
              return (
                <div
                  key={group.label}
                  className={`rounded-xl border transition-all duration-300 ${group.borderColor} ${group.bgColor}`}
                >
                  {/* Accordion Header */}
                  <button
                    onClick={() => toggleSection(group.label)}
                    className="w-full flex items-center justify-between px-5 py-4 cursor-pointer select-none group"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg bg-black/30 border border-current/10 ${group.color}`}>
                        {group.icon}
                      </div>
                      <div className="text-left">
                        <span className={`text-sm font-bold font-display ${group.color}`}>
                          {group.label}
                        </span>
                        <span className="ml-2 text-xs font-mono text-textSecondary">
                          ({group.records.length} {group.records.length === 1 ? 'dia' : 'dias'})
                        </span>
                      </div>
                    </div>
                    <div className={`transition-transform duration-200 ${group.color}`}>
                      {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </div>
                  </button>

                  {/* Accordion Content */}
                  {isExpanded && (
                    <div className="px-5 pb-5 space-y-4 animate-fadeIn">
                      {/* Explanation */}
                      <div className="bg-black/20 rounded-lg p-4 border border-zinc-800/40">
                        <p className="text-xs text-textSecondary leading-relaxed">
                          <strong className="text-zinc-300">O que significa:</strong>{' '}
                          {group.description}
                        </p>
                      </div>

                      {/* Dates list */}
                      <div className="space-y-2">
                        <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">
                          Datas registradas
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                          {group.records.map((rec, idx) => (
                            <div
                              key={idx}
                              className="flex items-center gap-3 bg-black/25 rounded-lg px-4 py-3 border border-zinc-800/30"
                            >
                              <div className="flex flex-col items-center min-w-[52px]">
                                <span className="text-[10px] text-zinc-500 uppercase font-bold">{rec.weekday}</span>
                                <span className="text-sm font-black font-mono text-white">{rec.date}</span>
                              </div>
                              <div className="h-6 w-px bg-zinc-800/60" />
                              <div className="flex flex-col flex-1 min-w-0">
                                {rec.occurrence ? (
                                  <span className="text-xs text-primary font-semibold truncate">{rec.occurrence}</span>
                                ) : (
                                  <span className="text-xs text-zinc-500 italic">Sem ocorrência</span>
                                )}
                                {rec.reason ? (
                                  <span className="text-[11px] text-textSecondary truncate" title={rec.reason}>
                                    {rec.reason}
                                  </span>
                                ) : null}
                                {(rec.status === 'INCONSISTENCIA') && (
                                  <span className="text-[10px] text-warning/80 mt-0.5">
                                    {!rec.first_period_entry && '⚠ Sem entrada 1°'}
                                    {!rec.first_period_exit && ' ⚠ Sem saída 1°'}
                                    {!rec.second_period_entry && rec.requires_second_period && ' ⚠ Sem entrada 2°'}
                                    {!rec.second_period_exit && rec.requires_second_period && ' ⚠ Sem saída 2°'}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Impact note for absences */}
                      {group.label === 'Faltas Injustificadas' && group.records.length > 0 && (
                        <div className="bg-error/5 rounded-lg p-4 border border-error/15 flex items-start gap-3">
                          <AlertCircle size={16} className="text-error shrink-0 mt-0.5" />
                          <div className="text-xs text-zinc-300 leading-relaxed">
                            <strong className="text-error">Impacto na folha:</strong>{' '}
                            {group.records.length} {group.records.length === 1 ? 'falta injustificada' : 'faltas injustificadas'} no período.
                            Serão descontadas do salário ({summary.absence_hours !== '00:00' ? `total de ${summary.absence_hours} horas` : 'total a calcular'}).
                            Semanas com faltas injustificadas também perdem o direito ao DSR (Descanso Semanal Remunerado).
                          </div>
                        </div>
                      )}

                      {/* Impact note for inconsistencies */}
                      {group.label === 'Inconsistências' && group.records.length > 0 && (
                        <div className="bg-warning/5 rounded-lg p-4 border border-warning/15 flex items-start gap-3">
                          <AlertCircle size={16} className="text-warning shrink-0 mt-0.5" />
                          <div className="text-xs text-zinc-300 leading-relaxed">
                            <strong className="text-warning">Ação necessária:</strong>{' '}
                            {group.records.length} {group.records.length === 1 ? 'registro inconsistente precisa' : 'registros inconsistentes precisam'} de tratamento manual.
                            Verifique se houve esquecimento de marcação ou problema no relógio de ponto e ajuste antes do fechamento da folha.
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Daily Records table section */}
      <div className="mt-8">
        <div className="mb-4">
          <h3 className="text-lg font-bold font-display text-white">Registros Diários</h3>
          <p className="text-xs text-textSecondary mt-0.5">Visão detalhada de cada dia registrado no espelho de ponto.</p>
        </div>
        <RecordsTable records={employee.records} />
      </div>
    </div>
  );
}

/* ─── Mini Stat Card Sub-component ─── */
type MiniStatCardProps = {
  label: string;
  value?: number;
  hours?: string;
  color: string;
};

function MiniStatCard({ label, value, hours, color }: MiniStatCardProps) {
  const colorMap: Record<string, { text: string; border: string; bg: string }> = {
    error:   { text: 'text-error',      border: 'border-error/20',   bg: 'bg-error/5' },
    warning: { text: 'text-warning',    border: 'border-warning/20', bg: 'bg-warning/5' },
    blue:    { text: 'text-blue-400',   border: 'border-blue-500/20', bg: 'bg-blue-500/5' },
    indigo:  { text: 'text-indigo-400', border: 'border-indigo-500/20', bg: 'bg-indigo-500/5' },
    success: { text: 'text-success',    border: 'border-success/20', bg: 'bg-success/5' },
    zinc:    { text: 'text-zinc-500',   border: 'border-zinc-800/40', bg: 'bg-zinc-900/20' },
  };

  const c = colorMap[color] || colorMap.zinc;
  const hasValue = (value !== undefined && value > 0) || (hours !== undefined && hours !== '00:00');

  return (
    <div className={`rounded-xl p-3.5 border text-center ${c.border} ${c.bg}`}>
      <p className="text-[9px] text-zinc-500 uppercase tracking-widest font-bold mb-1.5">{label}</p>
      {value !== undefined && (
        <p className={`text-xl font-black font-mono ${hasValue ? c.text : 'text-zinc-600'}`}>{value}</p>
      )}
      {hours !== undefined && value !== undefined && (
        <p className={`text-xs font-bold font-mono mt-0.5 ${hasValue ? c.text : 'text-zinc-600'}`}>
          <Timer size={10} className="inline mr-1" />
          {hours}
        </p>
      )}
      {hours !== undefined && value === undefined && (
        <p className={`text-xl font-black font-mono ${hasValue ? c.text : 'text-zinc-600'}`}>{hours}</p>
      )}
    </div>
  );
}
