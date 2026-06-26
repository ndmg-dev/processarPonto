import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { UploadPage } from './pages/UploadPage';
import { ResultPage } from './pages/ResultPage';
import { EmployeeDetailPage } from './pages/EmployeeDetailPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background text-textPrimary">
        <header className="bg-primary text-white p-4 shadow-md">
          <div className="container mx-auto flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Ponto Report</h1>
          </div>
        </header>
        <main className="container mx-auto p-4 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/result/:uploadId" element={<ResultPage />} />
            <Route path="/result/:uploadId/employee/:employeeId" element={<EmployeeDetailPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
