import '../../styles/metrics-panel.css';

const BORDER_MAP = {
  'border-l-surface-tint': 'metrics-panel__card--tint',
  'border-l-emerald-500':  'metrics-panel__card--emerald',
  'border-l-amber-500':    'metrics-panel__card--amber',
};

export function MetricsPanel({ result }) {
  if (!result) return null;

  const metrics = [
    { label: 'Objective Value', value: result.objective_value?.toLocaleString() ?? '\u2014', borderColor: 'border-l-surface-tint' },
    { label: 'Selected', value: `${result.selected_count}`, borderColor: 'border-l-emerald-500' },
    { label: 'Solve Time', value: result.solveTime ? `${result.solveTime}ms` : '\u2014', borderColor: 'border-l-amber-500' },
  ];

  return (
    <section className="metrics-panel">
      <h3 className="metrics-panel__heading">
        Solve Performance
      </h3>
      <div className="metrics-panel__grid">
        {metrics.map(m => (
          <div
            key={m.label}
            className={`metrics-panel__card ${BORDER_MAP[m.borderColor] || ''}`}
          >
            <p className="metrics-panel__label">
              {m.label}
            </p>
            <h5 className="metrics-panel__value">{m.value}</h5>
          </div>
        ))}
      </div>
    </section>
  );
}
