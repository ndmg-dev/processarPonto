import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCard } from '../components/UploadCard';
import { uploadFile } from '../api/client';

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

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold text-primary mb-4">Leitor de Espelho de Ponto</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Faça o upload do seu arquivo PDF contendo os espelhos de ponto. 
          O sistema irá ler, analisar e extrair todas as informações de forma estruturada.
        </p>
      </div>

      <UploadCard onUpload={handleUpload} loading={loading} />
      
      <div className="mt-16 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 p-1 rounded-md">💡</span> Como funciona?
        </h3>
        <ul className="list-disc list-inside space-y-2 text-gray-600 ml-2">
          <li>O sistema suporta PDFs com múltiplos colaboradores (uma página por colaborador).</li>
          <li>Jornadas de sábado ou turnos parciais não são penalizadas por falta de segundo período.</li>
          <li>Inconsistências são automaticamente detectadas e destacadas.</li>
          <li>Você poderá gerar um relatório consolidado em PDF no final.</li>
        </ul>
      </div>
    </div>
  );
}
