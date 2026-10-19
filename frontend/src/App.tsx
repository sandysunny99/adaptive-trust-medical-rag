import { Layout } from './components/Layout';
import { AnalyzePage } from './pages/AnalyzePage';
import { EvaluationPage } from './pages/EvaluationPage';
import { AuditPage } from './pages/AuditPage';
import { AboutPage } from './pages/AboutPage';
import { HistoryPage } from './pages/HistoryPage';
import { useHashRoute } from './routing/useHashRoute';

export default function App() {
  const { page, navigate, showResearchTabs } = useHashRoute();

  // Every page except Analyze mounts on demand.
  const renderOtherPage = () => {
    switch (page) {
      case 'history': return <HistoryPage />;
      case 'about': return <AboutPage />;
      case 'evaluation': return <EvaluationPage />;
      case 'audit': return <AuditPage />;
      default: return null;
    }
  };

  return (
    <Layout currentPage={page} onNavigate={navigate} showResearchTabs={showResearchTabs}>
      {/*
        Analyze stays mounted so an in-progress or finished analysis survives
        visits to other pages. `hidden` removes it from layout, the
        accessibility tree and the tab order while another page is shown.
      */}
      <div hidden={page !== 'analyze'}>
        <AnalyzePage />
      </div>
      {page !== 'analyze' && renderOtherPage()}
    </Layout>
  );
}
