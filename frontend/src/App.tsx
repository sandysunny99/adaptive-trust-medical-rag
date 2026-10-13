import { Layout } from './components/Layout';
import { WorkspacePage } from './pages/WorkspacePage';
import { EvaluationPage } from './pages/EvaluationPage';
import { AuditPage } from './pages/AuditPage';
import { OverviewPage } from './pages/OverviewPage';
import { HistoryPage } from './pages/HistoryPage';
import { useHashRoute } from './routing/useHashRoute';

export default function App() {
  const { page, navigate, showResearchTabs } = useHashRoute();

  const renderPage = () => {
    switch (page) {
      case 'history': return <HistoryPage />;
      // Temporary: the methodology content still lives in OverviewPage until the About page lands.
      case 'about': return <OverviewPage />;
      case 'evaluation': return <EvaluationPage />;
      case 'audit': return <AuditPage />;
      case 'analyze':
      default: return <WorkspacePage />;
    }
  };

  return (
    <Layout currentPage={page} onNavigate={navigate} showResearchTabs={showResearchTabs}>
      {renderPage()}
    </Layout>
  );
}
