import { Icon } from '../../components/shared/Icon';
import { DistHistogram } from './DistHistogram';
import { formatParamValue } from '../../utils/units';
import { InfoTooltip } from '../../components/shared/InfoTooltip';
import { FIELD_INFO } from './fieldInfo';
import '../../styles/param-card.css';

const PARAM_UNITS = {
  price:            { prefix: '$',  suffix: '' },
  weight:           { prefix: '',   suffix: 'kg' },
  volume:           { prefix: '',   suffix: 'm³' },
  demand:           { prefix: '',   suffix: 'units' },
  cost_per_watt:    { prefix: '$',  suffix: '/W' },
  labour_hours:     { prefix: '',   suffix: 'h' },
  efficiency:       { prefix: '',   suffix: '%' },
  throughput:       { prefix: '',   suffix: 'u/h' },
  sunlight_hours:   { prefix: '',   suffix: 'h' },
  machine_capacity: { prefix: '',   suffix: 'u/h' },
  material_cost:    { prefix: '$',  suffix: '' },
  degradation_rate: { prefix: '',   suffix: '%/yr' },
};

function getUnit(name) {
  return PARAM_UNITS[name] || { prefix: '', suffix: '' };
}

const PARAM_COLORS = ['#524e5c'];
const DISTRIBUTIONS = ['uniform', 'power', 'gaussian', 'geometric', 'step', 'segmented'];

const DENSITY_PRESETS = [
  { label: 'Full', step: 1 },
  { label: '1/2',  step: 2 },
  { label: '1/4',  step: 4 },
  { label: '1/8',  step: 8 },
];

function activePresetFor(seg) {
  if (seg.dist !== 'step') return 'custom';
  const step = seg.kwargs?.step;
  if (DENSITY_PRESETS.some(p => p.step === step)) return step;
  return 'custom';
}

function segPointCount(seg) {
  const range = (seg.max ?? 100) - (seg.min ?? 0);
  if (seg.dist === 'step') {
    const step = seg.kwargs?.step ?? 1;
    return step > 0 ? Math.floor(range / step) + 1 : 0;
  }
  return seg.kwargs?.resolution ?? 10;
}

export function ParamCard({ param, index, onChange, onRemove }) {
  const color = PARAM_COLORS[index % PARAM_COLORS.length];
  const { prefix, suffix } = getUnit(param.name);
  const bias       = param.dist_kwargs?.bias ?? 1.5;
  const resolution = param.dist_kwargs?.resolution ?? 10;
  const segments   = param.dist_kwargs?.segments ?? [];
  const midpoint   = param.dist_kwargs?.midpoint ?? ((param.min ?? 0) + (param.max ?? 100)) / 2;
  const skew       = param.dist_kwargs?.skew ?? 0;

  function update(field, value) {
    onChange({ ...param, [field]: value });
  }

  function updateKwarg(key, value) {
    onChange({ ...param, dist_kwargs: { ...param.dist_kwargs, [key]: value } });
  }

  function updateSegment(si, field, value) {
    const next = segments.map((s, i) =>
      i === si ? { ...s, [field]: value } : s
    );
    if (field === 'max' && si < next.length - 1) {
      next[si + 1] = { ...next[si + 1], min: value };
    }
    if (field === 'min' && si > 0) {
      next[si - 1] = { ...next[si - 1], max: value };
    }
    updateKwarg('segments', next);
  }

  function updateSegmentKwarg(si, key, value) {
    const next = segments.map((s, i) =>
      i === si ? { ...s, kwargs: { ...s.kwargs, [key]: value } } : s
    );
    updateKwarg('segments', next);
  }

  function addSegment() {
    const last = segments[segments.length - 1];
    const newSeg = last
      ? { min: last.max, max: last.max + 100, dist: 'step', kwargs: { step: 1 } }
      : { min: param.min ?? 0, max: param.max ?? 100, dist: 'step', kwargs: { step: 1 } };
    updateKwarg('segments', [...segments, newSeg]);
  }

  function applyPreset(si, step) {
    const next = segments.map((s, i) =>
      i === si ? { ...s, dist: 'step', kwargs: { step } } : s
    );
    updateKwarg('segments', next);
  }

  function setCustomStep(si, value) {
    const next = segments.map((s, i) =>
      i === si ? { ...s, dist: 'step', kwargs: { step: Math.max(1, value) } } : s
    );
    updateKwarg('segments', next);
  }

  function removeSegment(si) {
    updateKwarg('segments', segments.filter((_, i) => i !== si));
  }

  const isSegmented = param.dist === 'segmented';

  return (
    <div className="param-card">
      {/* Header */}
      <div className="param-card__header">
        <div className="param-card__header-left">
          <Icon name="drag_indicator" className="param-card__drag-icon" />
          <span className="param-card__name">{param.name}</span>
          <div className="param-card__dist-wrapper">
            <select
              className="param-card__dist-select"
              value={param.dist}
              onChange={(e) => update('dist', e.target.value)}
            >
              {DISTRIBUTIONS.map(d => (
                <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)} Distribution</option>
              ))}
            </select>
          </div>
        </div>
        <button className="param-card__remove-btn" onClick={onRemove}>
          <Icon name="delete" className="param-card__remove-icon" />
        </button>
      </div>

      {/* Body */}
      <div className="param-card__body">
        <div className="param-card__controls">
          {/* Min / Max */}
          <div className="param-card__row">
            <div className="param-card__field">
              <label className="param-card__label">
                {prefix ? `MIN (${prefix})` : suffix ? `MIN (${suffix})` : 'MIN'}
                {FIELD_INFO[param.name]?.range && <InfoTooltip text={FIELD_INFO[param.name].range} />}
              </label>
              <input
                type="number"
                className="param-card__input"
                value={param.min ?? ''}
                onChange={(e) => update('min', e.target.value === '' ? null : Number(e.target.value))}
              />
            </div>
            <div className="param-card__field">
              <label className="param-card__label">
                {prefix ? `MAX (${prefix})` : suffix ? `MAX (${suffix})` : 'MAX'}
              </label>
              <input
                type="number"
                className="param-card__input"
                value={param.max ?? ''}
                onChange={(e) => update('max', e.target.value === '' ? null : Number(e.target.value))}
              />
            </div>
          </div>

          {/* Resolution */}
          {!isSegmented && (
            <div className="param-card__field">
              <div className="param-card__slider-header">
                <label className="param-card__label">RESOLUTION</label>
                <span className="param-card__slider-value" style={{ color }}>{resolution}</span>
              </div>
              <input
                type="range" min="1" max="100" step="1"
                className="param-card__slider"
                style={{ accentColor: color }}
                value={resolution}
                onChange={(e) => updateKwarg('resolution', Number(e.target.value))}
              />
            </div>
          )}

          {/* Bias (power only) */}
          {param.dist === 'power' && (
            <div className="param-card__field">
              <div className="param-card__slider-header">
                <label className="param-card__label">BIAS</label>
                <span className="param-card__slider-value" style={{ color }}>{bias.toFixed(1)}</span>
              </div>
              <input
                type="range" min="0.1" max="3" step="0.1"
                className="param-card__slider"
                style={{ accentColor: color }}
                value={bias}
                onChange={(e) => updateKwarg('bias', Number(e.target.value))}
              />
              <div className="param-card__slider-hints">
                <span className="param-card__slider-hint">{bias < 1 ? '● ' : ''}dense at max</span>
                <span className="param-card__slider-hint">dense at min{bias >= 1 ? ' ●' : ''}</span>
              </div>
            </div>
          )}

          {/* Gaussian controls */}
          {param.dist === 'gaussian' && (
            <>
              <div className="param-card__field">
                <div className="param-card__slider-header">
                  <label className="param-card__label">MIDPOINT</label>
                  <span className="param-card__slider-value" style={{ color }}>
                    {formatParamValue(midpoint, param.name)}
                  </span>
                </div>
                <input
                  type="range"
                  min={param.min ?? 0}
                  max={param.max ?? 100}
                  step={((param.max ?? 100) - (param.min ?? 0)) / 200}
                  className="param-card__slider"
                  style={{ accentColor: color }}
                  value={midpoint}
                  onChange={(e) => updateKwarg('midpoint', Number(e.target.value))}
                />
              </div>
              <div className="param-card__field">
                <div className="param-card__slider-header">
                  <label className="param-card__label">SKEW</label>
                  <span className="param-card__slider-value" style={{ color }}>{skew.toFixed(1)}</span>
                </div>
                <input
                  type="range" min="-5" max="5" step="0.1"
                  className="param-card__slider"
                  style={{ accentColor: color }}
                  value={skew}
                  onChange={(e) => updateKwarg('skew', Number(e.target.value))}
                />
                <div className="param-card__slider-hints">
                  <span className="param-card__slider-hint">{skew < 0 ? '● ' : ''}left tail</span>
                  <span className="param-card__slider-hint">right tail{skew > 0 ? ' ●' : ''}</span>
                </div>
              </div>
            </>
          )}

          {/* Segment builder */}
          {isSegmented && (
            <div className="param-card__segments">
              <div className="param-card__segments-header">
                <label className="param-card__label">SEGMENTS</label>
                <button
                  className="param-card__add-seg-btn"
                  style={{ color }}
                  onClick={addSegment}
                >
                  + ADD
                </button>
              </div>
              {segments.length === 0 && (
                <p className="param-card__no-segments">No segments — add one above.</p>
              )}
              {segments.map((seg, si) => {
                const preset = activePresetFor(seg);
                const pts = segPointCount(seg);
                return (
                  <div key={si} className="param-card__segment">
                    {/* Range row */}
                    <div className="param-card__seg-range">
                      <input
                        type="number"
                        className={`param-card__seg-input ${si > 0 ? 'param-card__seg-input--readonly' : 'param-card__seg-input--editable'}`}
                        placeholder="min"
                        value={seg.min ?? ''}
                        readOnly={si > 0}
                        onChange={(e) => si === 0 && updateSegment(si, 'min', Number(e.target.value))}
                      />
                      <span className="param-card__seg-dash">—</span>
                      <input
                        type="number"
                        className="param-card__seg-input param-card__seg-input--editable"
                        placeholder="max"
                        value={seg.max ?? ''}
                        onChange={(e) => updateSegment(si, 'max', Number(e.target.value))}
                      />
                      <button
                        className="param-card__seg-remove-btn"
                        onClick={() => removeSegment(si)}
                      >
                        <Icon name="close" className="param-card__seg-remove-icon" />
                      </button>
                    </div>

                    {/* Density preset chips */}
                    <div className="param-card__density-row">
                      <span className="param-card__density-label">Density:</span>
                      {DENSITY_PRESETS.map(p => (
                        <button
                          key={p.step}
                          className={`param-card__density-chip ${
                            preset === p.step
                              ? 'param-card__density-chip--active'
                              : 'param-card__density-chip--inactive'
                          }`}
                          onClick={() => applyPreset(si, p.step)}
                        >
                          {p.label}
                        </button>
                      ))}
                      <div className="param-card__custom-group">
                        <button
                          className={`param-card__density-chip ${
                            preset === 'custom'
                              ? 'param-card__density-chip--active'
                              : 'param-card__density-chip--inactive'
                          }`}
                          onClick={() => setCustomStep(si, seg.kwargs?.step ?? 3)}
                        >
                          Custom
                        </button>
                        {preset === 'custom' && (
                          <input
                            type="number"
                            min="1" max="1000" step="1"
                            className="param-card__custom-input"
                            value={seg.kwargs?.step ?? 3}
                            onChange={(e) => setCustomStep(si, Number(e.target.value))}
                          />
                        )}
                      </div>
                    </div>

                    {/* Info line */}
                    <div className="param-card__seg-info">
                      <span>{pts} points</span>
                      <span className="param-card__seg-info-dot">&middot;</span>
                      <span>step = {seg.kwargs?.step ?? 1}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Histogram preview */}
        <div className="param-card__preview">
          {(() => {
            let histMin = param.min ?? 0;
            let histMax = param.max ?? 100;
            let histBars = Math.min(Math.max(resolution, 5), 50);
            if (isSegmented && segments.length > 0) {
              histMin = Math.min(...segments.map(s => s.min ?? 0));
              histMax = Math.max(...segments.map(s => s.max ?? 100));
              const totalPts = segments.reduce((sum, s) => sum + segPointCount(s), 0);
              histBars = Math.min(Math.max(totalPts, 10), 80);
            }
            return (
              <>
                <DistHistogram
                  dist={param.dist}
                  distKwargs={param.dist_kwargs ?? {}}
                  color={color}
                  bars={histBars}
                  min={histMin}
                  max={histMax}
                />
                <div className="param-card__range-labels">
                  <span className="param-card__range-label">
                    {formatParamValue(histMin, param.name)}
                  </span>
                  <span className="param-card__range-label">
                    {formatParamValue(histMax, param.name)}
                  </span>
                </div>
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
