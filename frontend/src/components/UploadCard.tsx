import { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, FileCheck2 } from 'lucide-react';

type UploadCardProps = {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
};

export function UploadCard({ onUpload, loading }: UploadCardProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    if (selectedFile.type !== 'application/pdf') {
      setError('Por favor, selecione apenas arquivos PDF.');
      setFile(null);
    } else {
      setError('');
      setFile(selectedFile);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const handleSubmit = () => {
    if (file) {
      onUpload(file).catch(err => {
        setError(err.response?.data?.detail || err.message || 'Erro ao processar');
      });
    }
  };

  return (
    <div className="bg-card rounded-2xl shadow-premium p-8 max-w-xl mx-auto border border-zinc-800/80 transition-all duration-300 hover:shadow-premium-hover">
      <h2 className="text-xl font-bold font-display text-center mb-6 text-white uppercase tracking-wider">
        Upload do Espelho de Ponto
      </h2>
      
      <div 
        className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-300 cursor-pointer ${
          dragActive 
            ? 'border-primary bg-primary/5 shadow-[0_0_20px_rgba(223,186,115,0.05)]' 
            : 'border-zinc-800 hover:border-primary/60 hover:bg-zinc-900/40'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
      >
        <input 
          ref={inputRef}
          type="file" 
          className="hidden" 
          accept="application/pdf" 
          onChange={handleChange} 
        />
        
        {file ? (
          <div className="flex flex-col items-center gap-4 animate-fadeIn">
            <div className="p-4 bg-primary/10 rounded-full text-primary border border-primary/20 shadow-[0_0_15px_rgba(223,186,115,0.1)]">
              <FileCheck2 size={40} />
            </div>
            <div>
              <p className="text-base font-semibold text-white truncate max-w-[280px]" title={file.name}>
                {file.name}
              </p>
              <p className="text-xs text-textSecondary mt-1">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-zinc-900/80 rounded-full text-textSecondary border border-zinc-800">
              <UploadCloud size={40} />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Arraste seu arquivo PDF aqui</p>
              <p className="text-xs text-textSecondary mt-1">Ou clique para navegar pelo sistema</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-error/10 text-error rounded-xl border border-error/20 flex items-center gap-3 animate-shake">
          <AlertCircle size={18} className="shrink-0" />
          <p className="text-xs font-semibold">{error}</p>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className={`w-full mt-6 py-4 rounded-xl font-bold font-display text-sm tracking-wider uppercase transition-all duration-300 select-none ${
          !file || loading 
            ? 'bg-zinc-800 text-zinc-500 border border-zinc-700/30 cursor-not-allowed' 
            : 'bg-gold-gradient text-background hover:bg-gold-gradient-hover active:scale-[0.98] shadow-md hover:shadow-lg font-black'
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2.5">
            <svg className="animate-spin h-4 w-4 text-background" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Analisando Documento...
          </span>
        ) : (
          'Processar Ponto'
        )}
      </button>
    </div>
  );
}
