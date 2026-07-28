import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getUploadResult, generateReport } from '../api/client';
import type { UploadResult } from '../types/point';
import { SummaryCards } from '../components/SummaryCards';
import { EmployeeCard } from '../components/EmployeeCard';
import { Download, ArrowLeft, Search } from 'lucide-react';

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
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div></div>;
  }

  if (!data) {
    return <div className="text-center mt-20 text-error font-bold text-xl">Dados não encontrados.</div>;
  }

  // Calculate totals
  let totalRecords = 0, absences = 0, vacations = 0, daysOff = 0, inconsistencies = 0, nightAdditionalMinutes = 0;
  data.employees.forEach(emp => {
    totalRecords += emp.records.length;
    absences += emp.summary.absence_days;
    vacations += emp.summary.vacation_days;
    daysOff += emp.summary.days_off;
    inconsistencies += emp.summary.inconsistencies;
    const [h, m] = (emp.summary.night_additional_total || '00:00').split(':').map(Number);
    nightAdditionalMinutes += h * 60 + m;
  });
  const nightAdditionalTotal = `${String(Math.floor(nightAdditionalMinutes / 60)).padStart(2, '0')}:${String(nightAdditionalMinutes % 60).padStart(2, '0')}`;

  const filteredEmployees = data.employees.filter(emp => {
    const term = search.toLowerCase();
    return emp.name.toLowerCase().includes(term) || emp.cpf.includes(term) || emp.role.toLowerCase().includes(term);
  });

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <Link to="/" className="flex items-center gap-2 text-secondary hover:underline mb-2">
            <ArrowLeft size={20} /> Voltar
          </Link>
          <h2 className="text-3xl font-bold text-textPrimary">Resultado do Processamento</h2>
          <p className="text-textSecondary">Arquivo: <span className="font-medium text-textPrimary">{data.file_name}</span></p>
        </div>
        <button
          onClick={handleGenerateReport}
          disabled={reportLoading}
          className="flex items-center gap-2 bg-secondary text-black px-5 py-2.5 rounded-lg font-bold shadow-md hover:bg-secondaryHover hover:shadow-lg transition-all disabled:opacity-50"
        >
          <Download size={20} />
          {reportLoading ? 'Gerando...' : 'Baixar Relatório PDF'}
        </button>
      </div>

      <SummaryCards 
        totalEmployees={data.total_employees}
        totalRecords={totalRecords}
        absences={absences}
        vacations={vacations}
        daysOff={daysOff}
        inconsistencies={inconsistencies}
        nightAdditionalTotal={nightAdditionalTotal}
      />

      <div className="bg-card rounded-xl shadow-sm border border-border p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-textPrimary">Colaboradores</h3>
          <div className="relative w-72">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-textMuted">
              <Search size={18} />
            </div>
            <input
              type="text"
              placeholder="Buscar nome, CPF ou cargo..."
              className="bg-surface border border-border text-textPrimary text-sm rounded-lg focus:ring-secondary focus:border-secondary block w-full pl-10 p-2.5 placeholder:text-textMuted"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        {filteredEmployees.length === 0 ? (
          <div className="text-center py-10 text-textSecondary">Nenhum colaborador encontrado com esse termo.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEmployees.map(emp => (
              <EmployeeCard key={emp.id} employee={emp} uploadId={data.upload_id} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
