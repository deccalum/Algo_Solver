import { Icon } from '../../components/shared/Icon';
import '../../styles/constraint-list.css';

export function ConstraintList({ constraints, params, onChange }) {
  function updateConstraint(idx, field, value) {
    onChange(constraints.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  }

  function addConstraint() {
    onChange([
      ...constraints,
      { name: `constraint_${constraints.length + 1}`, kind: 'sum_le', param_name: params[0] || '', bound: 1000 },
    ]);
  }

  function removeConstraint(idx) {
    onChange(constraints.filter((_, i) => i !== idx));
  }

  return (
    <section className="constraint-list">
      <h3 className="constraint-list__heading">
        Optimization Constraints
      </h3>
      <div className="constraint-list__items">
        {constraints.map((c, i) => (
          <div
            key={i}
            className="constraint-list__row"
          >
            <div className="constraint-list__row-left">
              <Icon name="drag_indicator" className="constraint-list__drag" />
              <div className="constraint-list__fields">
                <input
                  className="constraint-list__name-input"
                  value={c.name}
                  onChange={(e) => updateConstraint(i, 'name', e.target.value)}
                />
                <span className="constraint-list__kind-badge">
                  &le; {c.kind}
                </span>
                <select
                  className="constraint-list__param-select"
                  value={c.param_name}
                  onChange={(e) => updateConstraint(i, 'param_name', e.target.value)}
                >
                  {params.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
            </div>
            <div className="constraint-list__row-right">
              <div className="constraint-list__bound-group">
                <span className="constraint-list__bound-label">
                  bound
                </span>
                <input
                  type="number"
                  className="constraint-list__bound-input"
                  value={c.bound}
                  onChange={(e) => updateConstraint(i, 'bound', Number(e.target.value))}
                />
              </div>
              <button
                className="constraint-list__remove-btn"
                onClick={() => removeConstraint(i)}
              >
                <Icon name="close" />
              </button>
            </div>
          </div>
        ))}
        <button
          className="constraint-list__add-btn"
          onClick={addConstraint}
        >
          <Icon name="add" />
          ADD CONSTRAINT
        </button>
      </div>
    </section>
  );
}
