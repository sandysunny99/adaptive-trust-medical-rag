import { useState } from 'react';
import { Layout } from './components/Layout';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvidencePage } from './pages/EvidencePage';
import { SecurityPage } from './pages/SecurityPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { AuditPage } from './pages/AuditPage';
import { OverviewPage } from './pages/OverviewPage';

export type Page = 'overview' | 'workspace' | 'evidence' | 'security' | 'evaluation' | 'audit';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('workspace');

  const renderPage = () => {
    switch (currentPage) {
      case 'overview': return <OverviewPage />;
      case 'workspace': return <WorkspacePage />;
      case 'evidence': return <EvidencePage />;
      case 'security': return <SecurityPage />;
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
