import { useState } from 'react';
import { Layout } from './components/Layout';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvidencePage } from './pages/EvidencePage';
import { SecurityPage } from './pages/SecurityPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { AuditPage } from './pages/AuditPage';
import { OverviewPage } from './pages/OverviewPage';
import { HistoryPage } from './pages/HistoryPage';
import type { AnalysisResult } from './types';

export type Page = 'overview' | 'workspace' | 'history' | 'evidence' | 'security' | 'evaluation' | 'audit';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('workspace');
  const [currentResult, setCurrentResult] = useState<AnalysisResult | null>(null);

  const renderPage = () => {
    switch (currentPage) {
      case 'overview': return <OverviewPage />;
      case 'workspace': return <WorkspacePage result={currentResult} onResultChange={setCurrentResult} />;
      case 'history': return <HistoryPage onOpen={result => { setCurrentResult(result); setCurrentPage('workspace'); }} />;
      case 'evidence': return <EvidencePage result={currentResult} />;
      case 'security': return <SecurityPage result={currentResult} />;
      case 'evaluation': return <EvaluationPage />;
      case 'audit': return <AuditPage />;
      default: return <WorkspacePage />;
    }
  };

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderPage()}
    </Layout>
  );
}
