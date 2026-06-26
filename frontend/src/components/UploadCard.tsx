import { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle } from 'lucide-react';

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
    <div className="bg-card rounded-2xl shadow-xl p-8 max-w-xl mx-auto border border-gray-100 transition-all hover:shadow-2xl">
      <h2 className="text-2xl font-bold text-center mb-6 text-primary">Upload do Espelho de Ponto</h2>
      
      <div 
        className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-colors duration-200 cursor-pointer ${
          dragActive ? 'border-secondary bg-blue-50' : 'border-gray-300 hover:border-secondary hover:bg-gray-50'
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
          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-green-100 rounded-full text-success">
              <FileText size={48} />
            </div>
            <p className="text-lg font-medium text-gray-800">{file.name}</p>
            <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-blue-50 rounded-full text-secondary">
              <UploadCloud size={48} />
            </div>
            <p className="text-lg font-medium text-gray-700">Arraste e solte seu arquivo PDF aqui</p>
            <p className="text-sm text-gray-500">Ou clique para selecionar</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 text-error rounded-lg flex items-center gap-2">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className={`w-full mt-6 py-4 rounded-xl font-bold text-lg text-white transition-all transform ${
          !file || loading 
            ? 'bg-gray-400 cursor-not-allowed' 
            : 'bg-secondary hover:bg-blue-700 hover:shadow-lg active:scale-95'
        }`}
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processando PDF...
          </span>
        ) : (
          'Processar Ponto'
        )}
      </button>
    </div>
  );
}
