import { Icon } from '../../components/shared/Icon';
import { InfoTooltip } from '../../components/shared/InfoTooltip';
import { FIELD_INFO } from './fieldInfo';
import '../../styles/constraint-section.css';

const KINDS = [
  { value: 'sum_le', label: '≤ sum' },
  { value: 'sum_ge', label: '≥ sum' },
  { value: 'sum_eq', label: '= sum' },
];

const PARAM_UNITS = {
  price:         { prefix: '$',   suffix: '' },
  weight:        { prefix: '',    suffix: ' kg' },
  volume:        { prefix: '',    suffix: ' m³' },
  demand:        { prefix: '',    suffix: ' units' },
  material_cost: { prefix: '$',   suffix: '' },
  cost_per_watt: { prefix: '$',   suffix: '/W' },
  labour_hours:  { prefix: '',    suffix: ' h' },
  throughput:    { prefix: '',    suffix: ' u/h' },
};

function getUnit(paramName) {
  return PARAM_UNITS[paramName] || { prefix: '', suffix: '' };
}

export function ConstraintSection({ constraints, params, onChange }) {
  const CONSTRAINT_COLORS = {
    budget: '#5b35d5',
    space: '#0ea5c9',
  };

  function updateConstraint(idx, field, value) {
    onChange(constraints.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  }

  function removeConstraint(idx) {
    onChange(constraints.filter((_, i) => i !== idx));
  }

  function addConstraint() {
    if (params.length === 0) return;
    onChange([
      ...constraints,
      { name: `constraint_${constraints.length + 1}`, kind: 'sum_le', param_name: params[0].name, bound: 1000 },
    ]);
  }

  return (
    <div className="constraint-section">
      <div className="constraint-section__header">
        <span className="constraint-section__title">CONSTRAINTS</span>
      </div>
      <div className="constraint-section__grid">
        {constraints.map((c, i) => {
          const color = CONSTRAINT_COLORS[c.name] || '#5b35d5';
          return (
            <div key={i} className="constraint-card">
              <div className="constraint-card__header">
                <input
                  className="constraint-card__name-input"
                  style={{ color }}
                  value={c.name}
                  onChange={(e) => updateConstraint(i, 'name', e.target.value)}
                />
                <button
                  className="constraint-card__remove-btn"
                  onClick={() => removeConstraint(i)}
                >
                  <Icon name="close" className="constraint-card__remove-icon" />
                </button>
              </div>

              <div className="constraint-card__selectors">
                <select
                  className="constraint-card__select"
                  value={c.kind}
                  onChange={(e) => updateConstraint(i, 'kind', e.target.value)}
                >
                  {KINDS.map(k => <option key={k.value} value={k.value}>{k.label}</option>)}
                </select>
                <select
                  className="constraint-card__select"
                  value={c.param_name}
                  onChange={(e) => updateConstraint(i, 'param_name', e.target.value)}
                >
                  {params.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                </select>
              </div>

              {(() => {
                const { prefix, suffix } = getUnit(c.param_name);
                const info = FIELD_INFO[c.name] || FIELD_INFO[c.param_name];
                return (
                  <div className="constraint-card__bound">
                    <label className="constraint-card__bound-label">
                      BOUND{info?.bound && <InfoTooltip text={info.bound} />}
                    </label>
                    <div className="constraint-card__bound-row">
                      {prefix && (
                        <span className="constraint-card__bound-prefix">{prefix}</span>
                      )}
                      <input
                        type="number"
                        className="constraint-card__bound-input"
                        value={c.bound}
                        onChange={(e) => updateConstraint(i, 'bound', Number(e.target.value))}
                      />
                      {suffix && (
                        <span className="constraint-card__bound-suffix">{suffix}</span>
                      )}
                    </div>
                  </div>
                );
              })()}

              <div className="constraint-card__progress">
                <div
                  className="constraint-card__progress-fill"
                  style={{ width: '40%', backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <button
        className="constraint-section__add-btn"
        onClick={addConstraint}
      >
        + ADD CONSTRAINT
      </button>
    </div>
  );
}
