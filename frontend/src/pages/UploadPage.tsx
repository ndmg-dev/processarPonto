import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCard } from '../components/UploadCard';
import { uploadFile } from '../api/client';
import { Sparkles, Check } from 'lucide-react';

export function UploadPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const result = await uploadFile(file);
      navigate(`/result/${result.upload_id}`);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    'Suporta PDFs com múltiplos colaboradores (uma página por colaborador).',
    'Jornadas de sábado ou turnos parciais não são penalizadas por falta de segundo período.',
    'Inconsistências e faltas são automaticamente detectadas e destacadas com alertas visuais.',
    'Geração instantânea de relatório analítico consolidado em PDF para arquivamento ou impressão.'
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 md:py-16 px-4 animate-fadeIn">
      {/* Hero Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 px-3.5 py-1.5 rounded-full text-primary text-xs font-semibold tracking-wider uppercase mb-5">
          <Sparkles size={12} />
          Tecnologia Inteligente de Leitura
        </div>
        
        <h1 className="text-4xl md:text-5xl font-black font-display tracking-tight text-white mb-6">
          Leitor de Espelho de <span className="text-gold-gradient">Ponto Eletrônico</span>
        </h1>
        
        <p className="text-base text-textSecondary max-w-2xl mx-auto leading-relaxed">
          Faça o upload do seu arquivo PDF contendo os espelhos de ponto. 
          Nossa engine irá ler, analisar e extrair as jornadas, inconsistências e horas trabalhadas de forma imediata e estruturada.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="mb-14">
        <UploadCard onUpload={handleUpload} loading={loading} />
      </div>
      
      {/* Guidelines / How it works */}
      <div className="bg-card p-6 md:p-8 rounded-2xl border border-zinc-800/80 shadow-premium relative overflow-hidden">
        {/* Subtle glow background */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        
        <h3 className="text-base font-bold font-display text-white mb-6 flex items-center gap-2.5">
          <span className="text-primary font-bold">💡</span> Como funciona o processamento?
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {steps.map((step, idx) => (
            <div key={idx} className="flex gap-3 items-start bg-zinc-950/40 p-4 rounded-xl border border-zinc-900/50 hover:border-zinc-800 transition-colors">
              <div className="p-1 rounded bg-primary/15 text-primary shrink-0 mt-0.5 border border-primary/25">
                <Check size={12} className="stroke-[3]" />
              </div>
              <p className="text-xs text-textSecondary leading-relaxed">
                {step}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
