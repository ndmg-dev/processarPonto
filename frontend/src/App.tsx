import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { UploadPage } from './pages/UploadPage';
import { ResultPage } from './pages/ResultPage';
import { EmployeeDetailPage } from './pages/EmployeeDetailPage';
import { Shield } from 'lucide-react';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-textPrimary flex flex-col font-sans">
        {/* Header com Glassmorphism e toque Dourado/Prata */}
        <header className="sticky top-0 z-50 backdrop-blur-md bg-background/80 border-b border-zinc-800/80 transition-all duration-300">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-800 to-black border border-zinc-700/50 flex items-center justify-center transition-all duration-300 group-hover:border-primary/50 group-hover:shadow-[0_0_15px_rgba(223,186,115,0.15)]">
                <Shield className="w-5 h-5 text-primary transition-transform duration-300 group-hover:scale-110" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tracking-wider font-display text-white">
                  Processamento de <span className="text-gold-gradient font-black">Ponto - MG</span>
                </span>
              </div>
            </Link>
          </div>
          {/* Fina linha decorativa de gradiente dourado */}
          <div className="h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent w-full"></div>
        </header>

        {/* Conteúdo Principal */}
        <main className="flex-grow container mx-auto px-6 py-8 md:py-12 max-w-7xl">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/result/:uploadId" element={<ResultPage />} />
            <Route path="/result/:uploadId/employee/:employeeId" element={<EmployeeDetailPage />} />
          </Routes>
        </main>

        {/* Rodapé Premium */}
        <footer className="border-t border-zinc-800/60 py-6 bg-zinc-950/40 text-center text-xs text-textSecondary">
          <div className="container mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
            <p>&copy; {new Date().getFullYear()} Núcleo Digital - Mendonça Galvão. Todos os direitos reservados.</p>
            <p className="flex items-center gap-1.5 justify-center">
              Desenvolvido com excelência e<span className="text-primary font-bold">exclusividade</span>.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
