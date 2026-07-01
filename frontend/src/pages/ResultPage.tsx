import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUploadResult, generateReport } from '../api/client';
import type { UploadResult } from '../types/point';
import { SummaryCards } from '../components/SummaryCards';
import { EmployeeCard } from '../components/EmployeeCard';
import { Download, ArrowLeft, Search, FileDown } from 'lucide-react';

export function ResultPage() {
  const { uploadId } = useParams<{ uploadId: string }>();
  const [data, setData] = useState<UploadResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (uploadId) {
      getUploadResult(uploadId)
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [uploadId]);

  const handleGenerateReport = async () => {
    if (!uploadId) return;
    setReportLoading(true);
    try {
      const url = await generateReport(uploadId);
      window.open(url, '_blank');
    } catch (e) {
      console.error(e);
      alert('Erro ao gerar relatório');
    } finally {
      setReportLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-[50vh] gap-4">
        <div className="relative w-12 h-12">
          <div className="absolute inset-0 rounded-full border-2 border-zinc-800" />
          <div className="absolute inset-0 rounded-full border-2 border-t-primary border-r-primary animate-spin" />
        </div>
        <p className="text-sm text-textSecondary font-medium font-mono tracking-wider animate-pulse">Carregando painel consolidado...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 animate-fadeIn">
        <div className="text-error text-xl font-bold mb-3">Dados não encontrados</div>
        <p className="text-textSecondary text-sm mb-6">O link pode ser inválido ou o arquivo expirou.</p>
        <Link to="/" className="inline-flex items-center gap-2 text-primary hover:underline">
          <ArrowLeft size={16} /> Voltar para o início
        </Link>
      </div>
    );
  }

  // Calculate totals
  let totalRecords = 0, absences = 0, vacations = 0, daysOff = 0, inconsistencies = 0;
  data.employees.forEach(emp => {
    totalRecords += emp.records.length;
    absences += emp.summary.absence_days;
    vacations += emp.summary.vacation_days;
    daysOff += emp.summary.days_off;
    inconsistencies += emp.summary.inconsistencies;
  });

  const filteredEmployees = data.employees.filter(emp => {
    const term = search.toLowerCase();
    return emp.name.toLowerCase().includes(term) || emp.cpf.includes(term) || emp.role.toLowerCase().includes(term);
  });

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Bar with actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Link to="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-textSecondary hover:text-white mb-3 transition-colors group">
            <ArrowLeft size={14} className="transition-transform group-hover:-translate-x-0.5" /> Voltar
          </Link>
          <h2 className="text-2xl font-bold font-display text-white mb-1">
            Resultado do Processamento
          </h2>
          <p className="text-xs text-textSecondary">
            Arquivo processado: <span className="font-mono text-zinc-300 font-semibold">{data.file_name}</span>
          </p>
        </div>
        
        <button
          onClick={handleGenerateReport}
          disabled={reportLoading}
          className="w-full md:w-auto inline-flex items-center justify-center gap-2 bg-gold-gradient text-background px-6 py-3 rounded-xl font-bold font-display text-xs tracking-wider uppercase transition-all duration-300 hover:bg-gold-gradient-hover active:scale-[0.98] shadow-md hover:shadow-lg disabled:opacity-50 select-none cursor-pointer"
        >
          <FileDown size={16} />
          {reportLoading ? 'Gerando Relatório...' : 'Baixar Relatório Completo'}
        </button>
      </div>

      {/* Summary Analytics Cards */}
      <SummaryCards 
        totalEmployees={data.total_employees}
        totalRecords={totalRecords}
        absences={absences}
        vacations={vacations}
        daysOff={daysOff}
        inconsistencies={inconsistencies}
      />

      {/* Employees Section */}
      <div className="bg-card rounded-2xl border border-zinc-800/80 shadow-premium p-6 md:p-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h3 className="text-lg font-bold font-display text-white">Colaboradores</h3>
            <p className="text-xs text-textSecondary mt-0.5">Clique em um colaborador para ver seus registros individuais.</p>
          </div>
          
          <div className="relative w-full sm:w-80">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-zinc-500">
              <Search size={16} />
            </div>
            <input 
              type="text" 
              placeholder="Buscar colaborador, CPF ou cargo..." 
              className="bg-zinc-950/80 border border-zinc-800 text-white text-xs rounded-xl focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-10 pr-4 py-3 placeholder:text-zinc-600 transition-all font-sans"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        {filteredEmployees.length === 0 ? (
          <div className="text-center py-12 text-xs text-textSecondary font-mono border border-dashed border-zinc-850 rounded-xl">
            Nenhum colaborador corresponde aos critérios de busca.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredEmployees.map(emp => (
              <EmployeeCard key={emp.id} employee={emp} uploadId={data.upload_id} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
