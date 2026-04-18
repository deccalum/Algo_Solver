import { Icon } from '../../components/shared/Icon';
import '../../styles/objective-selector.css';

export function ObjectiveSelector({ params, objectiveParam, objectiveSense, onParamChange, onSenseChange }) {
  return (
    <section className="objective-selector">
      <h3 className="objective-selector__heading">
        Solver Objective
      </h3>
      <div className="objective-selector__card">
        <div className="objective-selector__pills">
          {params.map(p => (
            <button
              key={p}
              className={`objective-selector__pill ${objectiveParam === p
                  ? 'objective-selector__pill--active'
                  : 'objective-selector__pill--inactive'
                }`}
              onClick={() => onParamChange(p)}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="objective-selector__sense-row">
          <button
            className={`objective-selector__sense-btn ${objectiveSense === 'maximize' ? 'objective-selector__sense-btn--active' : ''}`}
            onClick={() => onSenseChange('maximize')}
          >
            <Icon name="trending_up" />
            MAXIMIZE
          </button>
          <button
            className={`objective-selector__sense-btn ${objectiveSense === 'minimize' ? 'objective-selector__sense-btn--active' : ''}`}
            onClick={() => onSenseChange('minimize')}
          >
            <Icon name="trending_down" />
            MINIMIZE
          </button>
        </div>
      </div>
    </section>
  );
}
