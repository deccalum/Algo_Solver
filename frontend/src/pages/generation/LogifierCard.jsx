import { InfoTooltip } from '../../components/shared/InfoTooltip';
import { FIELD_INFO } from './fieldInfo';
import '../../styles/logifier-card.css';

export const DEFAULT_LOGIFIER = {
  enabled: true,
  density_floor: 50.0,
  density_ceiling: 20000.0,
  price_per_litre_ceiling: 5000000.0,
  price_size_threshold: 0.0005,
};

function Field({ label, hint, tooltip, children }) {
  return (
    <div className="logifier-card__field">
      <label className="logifier-card__field-label">
        {label}{tooltip && <InfoTooltip text={tooltip} />}
      </label>
      {children}
      {hint && <p className="logifier-card__hint">{hint}</p>}
    </div>
  );
}

function NumInput({ value, onChange, step = 1, min, max }) {
  return (
    <input
      type="number"
      step={step} min={min} max={max}
      className="logifier-card__input"
      value={value}
      onChange={e => onChange(Number(e.target.value))}
    />
  );
}

export function LogifierCard({ config, onChange }) {
  function update(field, value) {
    onChange({ ...config, [field]: value });
  }

  return (
    <div className="logifier-card">
      <div className="logifier-card__header">
        <span className="logifier-card__title">REALISM FILTER</span>
        <label className="logifier-card__toggle-label">
          <div
            className={`logifier-card__toggle ${config.enabled ? 'logifier-card__toggle--on' : 'logifier-card__toggle--off'}`}
            onClick={() => update('enabled', !config.enabled)}
          >
            <div className={`logifier-card__toggle-knob ${config.enabled ? 'logifier-card__toggle-knob--on' : 'logifier-card__toggle-knob--off'}`} />
          </div>
          <span className="logifier-card__toggle-text">
            {config.enabled ? 'Active' : 'Off'}
          </span>
        </label>
      </div>

      {config.enabled ? (
        <div className="logifier-card__content">
          <p className="logifier-card__description">
            Probabilistic filter — items inside the band appear at full rate, items outside appear <em>less frequently</em>. The further outside, the fewer generated. No hard cutoffs.
          </p>

          <div className="logifier-card__grid">
            <Field
              label="Density floor (kg/m³)"
              hint="Below this, items decline in frequency. Aerogel ≈ 2, foam ≈ 50 kg/m³."
              tooltip={FIELD_INFO.density_floor.hint}
            >
              <NumInput
                value={config.density_floor}
                onChange={v => update('density_floor', v)}
                step={1} min={0.1} max={500}
              />
            </Field>
            <Field
              label="Density ceiling (kg/m³)"
              hint="Above this, items decline in frequency. Water = 1000, steel ≈ 8000, osmium ≈ 22000 kg/m³."
              tooltip={FIELD_INFO.density_ceiling.hint}
            >
              <NumInput
                value={config.density_ceiling}
                onChange={v => update('density_ceiling', v)}
                step={500} min={100} max={50000}
              />
            </Field>
          </div>

          <div className="logifier-card__grid">
            <Field
              label="Price/m³ ceiling ($/m³)"
              hint="Above this, tiny items decline in frequency. 0.001 m³ at $5000 = $5M/m³."
              tooltip={FIELD_INFO.price_per_m3.hint}
            >
              <NumInput
                value={config.price_per_litre_ceiling}
                onChange={v => update('price_per_litre_ceiling', v)}
                step={500000} min={10000}
              />
            </Field>
            <Field
              label="Size threshold (m³)"
              hint="Price/m³ rule only engages below this volume."
              tooltip={FIELD_INFO.size_threshold.hint}
            >
              <NumInput
                value={config.price_size_threshold}
                onChange={v => update('price_size_threshold', v)}
                step={0.0001} min={0.00001}
              />
            </Field>
          </div>
        </div>
      ) : (
        <div className="logifier-card__placeholder">
          <p className="logifier-card__placeholder-text">
            All combinations pass through — no plausibility checks applied.
          </p>
        </div>
      )}
    </div>
  );
}
