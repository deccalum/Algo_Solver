import '../../styles/combination-strip.css';

export function CombinationStrip({ count, perAxis, isOverLimit, filtered, onReset, onSave, saving }) {
  return (
    <div className="combination-strip">
      <div className="combination-strip__left">
        <div className="combination-strip__info">
          <span className="combination-strip__label">COMBINATIONS</span>
          <div className="combination-strip__values">
            <span className="combination-strip__count">
              {count != null ? count.toLocaleString() : '—'}
            </span>
            {perAxis && (
              <span className="combination-strip__per-axis">{perAxis}</span>
            )}
            {count != null && (
              <span className={`combination-strip__badge ${
                isOverLimit ? 'combination-strip__badge--over' : 'combination-strip__badge--ok'
              }`}>
                {isOverLimit ? 'OVER LIMIT' : 'OK'}
              </span>
            )}
            {filtered && count != null && (
              <span className="combination-strip__badge combination-strip__badge--filtered">
                FILTERED
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="combination-strip__right">
        <button
          className="combination-strip__reset-btn"
          onClick={onReset}
        >
          RESET
        </button>
        <button
          className="combination-strip__save-btn"
          onClick={onSave}
          disabled={saving || isOverLimit}
        >
          {saving ? 'GENERATING...' : 'SAVE & SOLVE'}
        </button>
      </div>
    </div>
  );
}
