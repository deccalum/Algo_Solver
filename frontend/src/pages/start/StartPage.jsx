import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getTemplates, getRuns, getSolves } from '../../api/client';
import { TemplateCard } from './TemplateCard';
import { HowItWorks } from './HowItWorks';
import { RecentActivity } from './RecentActivity';
import '../../styles/start-page.css';

export function StartPage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [runs, setRuns] = useState([]);
  const [solves, setSolves] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getTemplates().catch(() => []),
      getRuns(5).catch(() => []),
      getSolves(5).catch(() => []),
    ]).then(([t, r, s]) => {
      setTemplates(t);
      setRuns(r);
      setSolves(s);
      setLoading(false);
    });
  }, []);

  function handleSelect(templateName) {
    if (templateName === 'solar_panel') {
      navigate('/solar');
    } else {
      navigate('/generation', { state: { template: templateName } });
    }
  }

  if (loading) {
    return (
      <div className="start-page">
        <div className="start-page__loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="start-page">
      {/* Template Selection */}
      <section>
        <div className="start-page__section-header">
          <h2 className="start-page__section-label">
            SELECT TEMPLATE
          </h2>
        </div>
        <div className="start-page__grid">
          {templates.map(t => (
            <TemplateCard key={t.name} template={t} onSelect={handleSelect} />
          ))}
        </div>
      </section>

      <HowItWorks />
      <RecentActivity runs={runs} solves={solves} />
    </div>
  );
}
