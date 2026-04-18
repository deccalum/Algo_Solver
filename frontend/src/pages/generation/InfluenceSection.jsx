import { Icon } from '../../components/shared/Icon';
import '../../styles/influence-section.css';

export function InfluenceSection({ influences, params, onChange }) {
  function addInfluence() {
    if (params.length < 2) return;
    onChange([
      ...influences,
      { source: params[0].name, target: params[1].name, fn: 'scale', kwargs: { factor: -0.001 } },
    ]);
  }

  function removeInfluence(idx) {
    onChange(influences.filter((_, i) => i !== idx));
  }

  function updateInfluence(idx, field, value) {
    const updated = influences.map((inf, i) =>
      i === idx ? { ...inf, [field]: value } : inf
    );
    onChange(updated);
  }

  return (
    <div className="influence-section">
      <div className="influence-section__header">
        <span className="influence-section__title">INFLUENCES</span>
      </div>

      {influences.map((inf, i) => (
        <div key={i} className="influence-card">
          <div className="influence-card__body">
            <div className="influence-card__connector">
              <select
                className="influence-card__source-select"
                value={inf.source}
                onChange={(e) => updateInfluence(i, 'source', e.target.value)}
              >
                {params.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
              </select>

              <div className="influence-card__line" />
              <div className="influence-card__arrow-label">
                &rarr; {inf.fn}s &rarr;
              </div>
              <div className="influence-card__line" />

              <select
                className="influence-card__target-select"
                value={inf.target}
                onChange={(e) => updateInfluence(i, 'target', e.target.value)}
              >
                {params.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
              </select>
            </div>
            <div className="influence-card__meta">
              <span className="influence-card__factor">
                factor: {inf.kwargs?.factor ?? 0}
              </span>
              <button
                className="influence-card__remove-btn"
                onClick={() => removeInfluence(i)}
              >
                <Icon name="close" className="influence-card__remove-icon" />
              </button>
            </div>
          </div>
        </div>
      ))}

      <button
        className="influence-section__add-btn"
        onClick={addInfluence}
      >
        + ADD INFLUENCE
      </button>
    </div>
  );
}
