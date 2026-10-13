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

export type Page = 'overview' | 'workspace' | 'evidence' | 'security' | 'evaluation' | 'audit' | 'history';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('workspace');
  const [latestResult, setLatestResult] = useState<AnalysisResult | null>(null);

  const renderPage = () => {
    switch (currentPage) {
      case 'overview': return <OverviewPage />;
      case 'workspace': return <WorkspacePage onResultComplete={setLatestResult} />;
      case 'evidence': return <EvidencePage latestResult={latestResult} />;
      case 'security': return <SecurityPage latestResult={latestResult} />;
      case 'evaluation': return <EvaluationPage />;
      case 'audit': return <AuditPage />;
      case 'history': return <HistoryPage />;
      default: return <WorkspacePage onResultComplete={setLatestResult} />;
    }
  };

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderPage()}
    </Layout>
  );
}
