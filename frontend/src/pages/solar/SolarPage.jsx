import { useState } from 'react';
import { getSolarPsh, postSolarSolve } from '../../api/client';
import '../../styles/solar-page.css';

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(n, decimals = 2) {
  if (n == null || isNaN(n)) return '—';
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtMoney(n) {
  if (n == null || isNaN(n)) return '—';
  return '$' + n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function fmtLoan(sel) {
  const years = sel.loan_term_years;
  const rate  = sel.interest_rate_pct;
  if (!years) return 'Cash';
  return `${years}yr @ ${rate}%`;
}

function fmtLoanFull(sel) {
  const years = sel.loan_term_years;
  const rate  = sel.interest_rate_pct;
  if (!years) return 'Cash purchase';
  return `${years}-yr loan at ${rate}%`;
}

// ── Sub-components ────────────────────────────────────────────────────────────
function SectionHeader({ title, sub }) {
  return (
    <div className="solar-section__header">
      <span className="solar-section__title">{title}</span>
      {sub && <span className="solar-section__sub">{sub}</span>}
    </div>
  );
}

function Field({ label, children, hint }) {
  return (
    <label className="solar-field">
      <span className="solar-field__label">{label}</span>
      {children}
      {hint && <span className="solar-field__hint">{hint}</span>}
    </label>
  );
}

function NumberInput({ value, onChange, min, max, step = 'any', placeholder }) {
  return (
    <input
      className="solar-input"
      type="number"
      value={value}
      min={min}
      max={max}
      step={step}
      placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
    />
  );
}

// ── Location section ──────────────────────────────────────────────────────────
function LocationSection({ cfg, onChange }) {
  const [pshData, setPshData] = useState(null);
  const [busy,    setBusy]    = useState(false);
  const [error,   setError]   = useState(null);

  async function handleLookup() {
    const lat = parseFloat(cfg.lat);
    if (isNaN(lat) || lat < -90 || lat > 90) {
      setError('Enter a valid latitude (−90 to +90).');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const tilt    = cfg.tilt    !== '' ? parseFloat(cfg.tilt)    : undefined;
      const azimuth = cfg.azimuth !== '' ? parseFloat(cfg.azimuth) : undefined;
      const data    = await getSolarPsh(lat, tilt, azimuth);
      setPshData(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const latNum   = parseFloat(cfg.lat);
  const autoTilt = !isNaN(latNum) ? Math.abs(latNum).toFixed(0) : '|lat|';

  return (
    <div className="solar-section">
      <SectionHeader title="LOCATION" sub="Where will the panels be installed?" />
      <div className="solar-section__body">
        <div className="solar-row">
          <Field label="Latitude" hint="−90 to +90 (e.g. 51.5 = London)">
            <NumberInput
              value={cfg.lat}
              onChange={v => onChange('lat', v)}
              min={-90} max={90} step={0.01}
              placeholder="e.g. 51.5"
            />
          </Field>
          <Field label="Tilt °" hint={`blank = auto (${autoTilt}°)`}>
            <NumberInput
              value={cfg.tilt}
              onChange={v => onChange('tilt', v)}
              min={0} max={90} step={1}
              placeholder={`auto (${autoTilt}°)`}
            />
          </Field>
          <Field label="Azimuth °" hint="blank = optimal direction">
            <NumberInput
              value={cfg.azimuth}
              onChange={v => onChange('azimuth', v)}
              min={-180} max={180} step={1}
              placeholder="0 = south (NH)"
            />
          </Field>
          <button
            className="solar-btn solar-btn--secondary"
            onClick={handleLookup}
            disabled={busy || cfg.lat === ''}
          >
            {busy ? '…' : 'LOOK UP'}
          </button>
        </div>

        {error && <p className="solar-error">{error}</p>}

        {pshData && (
          <div className="solar-psh-result">
            <div className="solar-psh-result__stat">
              <span className="solar-psh-result__label">Annual avg</span>
              <strong className="solar-psh-result__value">{pshData.annual_avg_psh} h/day</strong>
            </div>
            <div className="solar-psh-result__stat">
              <span className="solar-psh-result__label">Seasonal range</span>
              <strong className="solar-psh-result__value">
                {pshData.seasonal_min_psh}-{pshData.seasonal_max_psh} h/day
              </strong>
            </div>
            <div className="solar-psh-result__stat">
              <span className="solar-psh-result__label">Optimal facing</span>
              <strong className="solar-psh-result__value">{pshData.optimal_azimuth}</strong>
            </div>
            {pshData.azimuth_gain_pct > 0 && (
              <div className="solar-psh-result__stat solar-psh-result__stat--warn">
                <span className="solar-psh-result__label">vs optimal</span>
                <strong className="solar-psh-result__value">−{pshData.azimuth_gain_pct}%</strong>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Cumulative savings SVG chart ──────────────────────────────────────────────
function SavingsChart({ sel, lifetime, annualSavings, systemCost }) {
  if (!sel || !lifetime || !annualSavings || !systemCost) return null;

  const loanYears     = sel.loan_term_years ?? 0;
  const monthlyPayment = sel.monthly_payment ?? 0;

  // Compute cumulative net at each year
  const years = Array.from({ length: lifetime + 1 }, (_, i) => i);
  const netValues = years.map(y => {
    const grossSavings = annualSavings * y;
    let totalPaid;
    if (loanYears === 0) {
      // Cash: full cost at year 0
      totalPaid = systemCost;
    } else {
      // Loan: monthly payments until loan is paid off
      totalPaid = Math.min(y, loanYears) * monthlyPayment * 12;
    }
    return grossSavings - totalPaid;
  });

  const minNet = Math.min(...netValues);
  const maxNet = Math.max(...netValues);
  const range  = maxNet - minNet || 1;

  const W = 600, H = 160;
  const pad = { top: 10, right: 12, bottom: 22, left: 56 };
  const iW = W - pad.left - pad.right;
  const iH = H - pad.top - pad.bottom;

  const toX = y => pad.left + (y / lifetime) * iW;
  const toY = v => pad.top + iH - ((v - minNet) / range) * iH;

  const zeroY = toY(0);

  const pts = netValues.map((v, i) => `${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');

  // Find payback year (first year where net > 0)
  const paybackYear = netValues.findIndex(v => v >= 0);

  // Y-axis ticks
  const yTicks = [minNet, 0, maxNet].filter((v, i, arr) =>
    arr.indexOf(v) === i && Math.abs(v) > range * 0.05
  );

  // X-axis ticks: 0, 5, 10, 15, 20, 25 (or fewer)
  const xStep = lifetime <= 15 ? 5 : 5;
  const xTicks = Array.from({ length: Math.floor(lifetime / xStep) + 1 }, (_, i) => i * xStep).filter(v => v <= lifetime);

  return (
    <div className="solar-chart">
      <div className="solar-chart__title">CUMULATIVE NET VALUE OVER SYSTEM LIFETIME</div>
      <svg className="solar-chart__svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        {/* Zero line */}
        {minNet < 0 && maxNet > 0 && (
          <line x1={pad.left} y1={zeroY} x2={W - pad.right} y2={zeroY}
            stroke="rgba(148,163,184,0.5)" strokeDasharray="4 3" strokeWidth="1" />
        )}

        {/* Y-axis ticks */}
        {yTicks.map((v, i) => {
          const y = toY(v);
          const label = v >= 1000 ? `$${(v / 1000).toFixed(0)}k`
                      : v <= -1000 ? `-$${Math.abs(v / 1000).toFixed(0)}k`
                      : `$${v.toFixed(0)}`;
          return (
            <g key={i}>
              <line x1={pad.left - 3} y1={y} x2={pad.left} y2={y}
                stroke="#94a3b8" strokeWidth="1" />
              <text x={pad.left - 5} y={y + 3.5} textAnchor="end"
                fontSize="9" fill="#94a3b8">{label}</text>
            </g>
          );
        })}

        {/* X-axis ticks */}
        {xTicks.map(y => (
          <g key={y}>
            <line x1={toX(y)} y1={H - pad.bottom} x2={toX(y)} y2={H - pad.bottom + 3}
              stroke="#94a3b8" strokeWidth="1" />
            <text x={toX(y)} y={H - pad.bottom + 12} textAnchor="middle"
              fontSize="9" fill="#94a3b8">{y}yr</text>
          </g>
        ))}

        {/* Area fill — below zero = red, above zero = green */}
        {minNet < 0 && (
          <clipPath id="solar-below">
            <rect x={pad.left} y={zeroY} width={iW} height={iH - (zeroY - pad.top)} />
          </clipPath>
        )}
        <clipPath id="solar-above">
          <rect x={pad.left} y={pad.top} width={iW} height={Math.max(0, zeroY - pad.top)} />
        </clipPath>

        {/* Line */}
        <polyline points={pts} fill="none" stroke="#f59e0b" strokeWidth="2" />

        {/* Shaded areas */}
        <polyline
          points={`${pts} ${toX(lifetime).toFixed(1)},${zeroY.toFixed(1)} ${toX(0).toFixed(1)},${zeroY.toFixed(1)}`}
          fill="rgba(34,197,94,0.12)" stroke="none"
          clipPath="url(#solar-above)"
        />
        {minNet < 0 && (
          <polyline
            points={`${pts} ${toX(lifetime).toFixed(1)},${zeroY.toFixed(1)} ${toX(0).toFixed(1)},${zeroY.toFixed(1)}`}
            fill="rgba(239,68,68,0.10)" stroke="none"
            clipPath="url(#solar-below)"
          />
        )}

        {/* Payback dot */}
        {paybackYear > 0 && paybackYear < lifetime && (
          <g>
            <circle cx={toX(paybackYear).toFixed(1)} cy={zeroY.toFixed(1)} r="5"
              fill="#f59e0b" />
            <text x={toX(paybackYear)} y={zeroY - 8} textAnchor="middle"
              fontSize="9" fill="#f59e0b" fontWeight="700">
              Payback yr {paybackYear}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

// ── Loan amortization table ───────────────────────────────────────────────────
function AmortizationTable({ sel, lifetime, annualSavings, systemCost }) {
  if (!sel || !lifetime || !annualSavings) return null;
  const loanYears      = sel.loan_term_years ?? 0;
  const monthlyPayment = sel.monthly_payment ?? 0;

  // Build year rows
  const rows = [];
  let cumSavings = 0;
  let totalPaid  = loanYears === 0 ? systemCost : 0;  // cash paid up front

  for (let y = 1; y <= lifetime; y++) {
    const annualPayment = (loanYears > 0 && y <= loanYears) ? monthlyPayment * 12 : 0;
    cumSavings += annualSavings;
    totalPaid  += annualPayment;
    const net   = cumSavings - totalPaid - (loanYears === 0 ? 0 : 0);  // already baked in
    // For cash: net = cumSavings - systemCost; for loan: net = cumSavings - payments so far
    const netCalc = loanYears === 0
      ? cumSavings - systemCost
      : cumSavings - totalPaid;

    rows.push({ year: y, annualSavings, annualPayment, cumSavings, totalPaid: loanYears === 0 ? systemCost : totalPaid, net: netCalc });
  }

  const paybackRow = rows.find(r => r.net >= 0);

  return (
    <div className="solar-amort">
      <div className="solar-amort__title">
        LOAN AMORTIZATION
        {paybackRow && (
          <span className="solar-amort__payback"> — payback in year {paybackRow.year}</span>
        )}
      </div>
      <div className="solar-amort__scroll">
        <table className="solar-amort__table">
          <thead>
            <tr>
              <th>Year</th>
              <th>Annual savings</th>
              {loanYears > 0 && <th>Annual payment</th>}
              <th>Cumul. savings</th>
              {loanYears > 0 && <th>Total paid</th>}
              <th>Net position</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.year} className={r.net >= 0 && rows[r.year - 2]?.net < 0 ? 'solar-amort__row--payback' : ''}>
                <td>{r.year}</td>
                <td className="solar-amort__positive">{fmtMoney(r.annualSavings)}</td>
                {loanYears > 0 && (
                  <td className={r.annualPayment > 0 ? 'solar-amort__negative' : 'solar-amort__muted'}>
                    {r.annualPayment > 0 ? fmtMoney(r.annualPayment) : '—'}
                  </td>
                )}
                <td>{fmtMoney(r.cumSavings)}</td>
                {loanYears > 0 && <td>{fmtMoney(r.totalPaid)}</td>}
                <td className={r.net >= 0 ? 'solar-amort__positive' : 'solar-amort__negative'}>
                  {fmtMoney(r.net)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Alternatives section ──────────────────────────────────────────────────────
function AlternativesSection({ alternatives }) {
  if (!alternatives || alternatives.length === 0) return null;

  return (
    <div className="solar-results__table-section">
      <div className="solar-results__table-title">
        RUNNER-UP CONFIGURATIONS
        <span className="solar-results__table-sub"> — next best alternatives by net lifetime value</span>
      </div>
      <div className="solar-results__table-scroll">
        <table className="solar-results__table">
          <thead>
            <tr>
              <th>#</th>
              <th>Eff (%)</th>
              <th>$/W</th>
              <th>Battery</th>
              <th>Financing</th>
              <th>System cost</th>
              <th>Annual savings</th>
              <th>Net value</th>
            </tr>
          </thead>
          <tbody>
            {alternatives.map((s, i) => (
              <tr key={s.id ?? i}>
                <td className="solar-results__table-rank">{i + 2}</td>
                <td>{fmt(s.efficiency, 0)}</td>
                <td>{fmt(s.cost_per_watt, 3)}</td>
                <td>{s.battery_kwh > 0 ? `${s.battery_kwh} kWh` : 'None'}</td>
                <td>{fmtLoan(s)}</td>
                <td>{fmtMoney(s.system_cost)}</td>
                <td className="solar-results__fin-value--positive">{fmtMoney(s.annual_savings)}/yr</td>
                <td>{fmtMoney(s.net_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
const DEFAULT_CONFIG = {
  lat:                  '',
  tilt:                 '',
  azimuth:              '',
  electricity_rate:     0.28,
  feed_in_rate:         0.08,
  upfront_budget:       10000,
  max_monthly:          '',
  battery_cost_per_kwh: 800,
  roof_area_m2:         30,
  panel_area_m2:        1.7,
  system_lifetime:      25,
  daily_kwh:            10,
};

export function SolarPage() {
  const [cfg,     setCfg]     = useState(DEFAULT_CONFIG);
  const [result,  setResult]  = useState(null);
  const [solving, setSolving] = useState(false);
  const [error,   setError]   = useState(null);

  function onChange(field, value) {
    setCfg(prev => ({ ...prev, [field]: value }));
  }

  async function handleSolve() {
    const lat = parseFloat(cfg.lat);
    if (isNaN(lat) || lat < -90 || lat > 90) {
      setError('Enter a valid latitude (−90 to +90) to continue.');
      return;
    }
    setSolving(true);
    setError(null);
    setResult(null);
    try {
      const req = {
        lat,
        tilt:                 cfg.tilt    !== '' ? parseFloat(cfg.tilt)    : null,
        azimuth:              cfg.azimuth !== '' ? parseFloat(cfg.azimuth) : null,
        electricity_rate:     parseFloat(cfg.electricity_rate) || 0.28,
        feed_in_rate:         parseFloat(cfg.feed_in_rate)     || 0.08,
        upfront_budget:       parseFloat(cfg.upfront_budget)   || 10000,
        max_monthly:          cfg.max_monthly !== '' ? parseFloat(cfg.max_monthly) : null,
        battery_cost_per_kwh: parseFloat(cfg.battery_cost_per_kwh) || 800,
        roof_area_m2:         parseFloat(cfg.roof_area_m2)    || 30,
        panel_area_m2:        parseFloat(cfg.panel_area_m2)   || 1.7,
        system_lifetime:      parseInt(cfg.system_lifetime)   || 25,
        daily_kwh:            parseFloat(cfg.daily_kwh)       || 10,
      };
      const data = await postSolarSolve(req);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setSolving(false);
    }
  }

  return (
    <div className="solar-page">
      <div className="solar-page__header">
        <h1 className="solar-page__title">HOME SOLAR ADVISOR</h1>
        <p className="solar-page__subtitle">
          The solver explores every combination of panel quality, battery size (0-20 kWh),
          and financing plan (cash or 10/20/25-yr loan at 3-7%) to find the system
          that maximises your net lifetime savings.
        </p>
      </div>

      <div className="solar-page__layout">
        {/* ── Left: Form ──────────────────────────────────────────────────── */}
        <div className="solar-page__form">

          <LocationSection cfg={cfg} onChange={onChange} />

          {/* Financials */}
          <div className="solar-section">
            <SectionHeader title="FINANCIALS" sub="Tariffs and budget" />
            <div className="solar-section__body">
              <div className="solar-row">
                <Field label="Electricity rate ($/kWh)" hint="Your current grid price">
                  <NumberInput value={cfg.electricity_rate} onChange={v => onChange('electricity_rate', v)}
                    min={0} max={5} step={0.01} placeholder="0.28" />
                </Field>
                <Field label="Feed-in tariff ($/kWh)" hint="Grid sell-back rate">
                  <NumberInput value={cfg.feed_in_rate} onChange={v => onChange('feed_in_rate', v)}
                    min={0} max={5} step={0.01} placeholder="0.08" />
                </Field>
              </div>
              <div className="solar-row">
                <Field label="Budget ($)" hint="Max system cost (cash or loan principal)">
                  <NumberInput value={cfg.upfront_budget} onChange={v => onChange('upfront_budget', v)}
                    min={0} step={500} placeholder="10000" />
                </Field>
                <Field label="Monthly cap ($)" hint="Optional: limit loan repayments">
                  <NumberInput value={cfg.max_monthly} onChange={v => onChange('max_monthly', v)}
                    min={0} step={10} placeholder="no limit" />
                </Field>
              </div>
              <div className="solar-row">
                <Field label="Battery price ($/kWh)" hint="Cost of storage hardware">
                  <NumberInput value={cfg.battery_cost_per_kwh} onChange={v => onChange('battery_cost_per_kwh', v)}
                    min={100} max={2000} step={50} placeholder="800" />
                </Field>
              </div>
            </div>
          </div>

          {/* System */}
          <div className="solar-section">
            <SectionHeader title="SYSTEM" sub="Roof and household" />
            <div className="solar-section__body">
              <div className="solar-row">
                <Field label="Roof area (m²)">
                  <NumberInput value={cfg.roof_area_m2} onChange={v => onChange('roof_area_m2', v)}
                    min={1} max={500} step={1} placeholder="30" />
                </Field>
                <Field label="Panel size (m²)" hint="Standard ≈ 1.7 m²">
                  <NumberInput value={cfg.panel_area_m2} onChange={v => onChange('panel_area_m2', v)}
                    min={0.5} max={5} step={0.1} placeholder="1.7" />
                </Field>
                <Field label="Daily use (kWh)" hint="Household consumption">
                  <NumberInput value={cfg.daily_kwh} onChange={v => onChange('daily_kwh', v)}
                    min={1} max={200} step={0.5} placeholder="10" />
                </Field>
                <Field label="Lifetime (yr)">
                  <NumberInput value={cfg.system_lifetime} onChange={v => onChange('system_lifetime', v)}
                    min={5} max={40} step={1} placeholder="25" />
                </Field>
              </div>
              <p className="solar-note">
                Panel count: up to {Math.floor((parseFloat(cfg.roof_area_m2) || 30) /
                  (parseFloat(cfg.panel_area_m2) || 1.7))} panels on your roof.
              </p>
            </div>
          </div>

          {/* Solver info box */}
          <div className="solar-explores">
            <div className="solar-explores__label">SOLVER EXPLORES</div>
            <div className="solar-explores__grid">
              <span>Efficiency: 15-23%</span>
              <span>Panel cost: $0.20-$0.80/W</span>
              <span>Degradation: 0.3-0.8%/yr</span>
              <span>Battery: 0, 5, 10, 15, 20 kWh</span>
              <span>Loan: cash · 10yr · 20yr · 25yr</span>
              <span>Rate: 3% · 5% · 7% APR</span>
            </div>
          </div>

          {error && <p className="solar-error solar-error--main">{error}</p>}

          <button
            className="solar-btn solar-btn--primary solar-btn--cta"
            onClick={handleSolve}
            disabled={solving}
          >
            {solving ? 'ANALYSING…' : 'FIND BEST SYSTEM'}
          </button>
        </div>

        {/* ── Right: Results ──────────────────────────────────────────────── */}
        <div className="solar-page__results">
          {!result && !solving && (
            <div className="solar-results-placeholder">
              <span className="solar-results-placeholder__icon">☀</span>
              <p className="solar-results-placeholder__text">
                Fill in your location and budget, then click <strong>FIND BEST SYSTEM</strong>.
              </p>
            </div>
          )}

          {solving && (
            <div className="solar-results-placeholder">
              <span className="solar-results-placeholder__icon solar-results-placeholder__icon--spin">⟳</span>
              <p className="solar-results-placeholder__text">
                Evaluating {' '}
                <strong>
                  {Math.floor((parseFloat(cfg.roof_area_m2) || 30) / (parseFloat(cfg.panel_area_m2) || 1.7)) > 0
                    ? '~3 000'
                    : '…'}
                </strong>
                {' '} configurations…
              </p>
            </div>
          )}

          {result && <SolarResults result={result} />}
        </div>
      </div>
    </div>
  );
}

// ── Results panel ─────────────────────────────────────────────────────────────
function SolarResults({ result }) {
  const sel = result.selections?.[0] ?? {};
  const [showAmort, setShowAmort] = useState(false);

  const batteryLabel  = sel.battery_kwh > 0 ? `${sel.battery_kwh} kWh` : 'None';
  const loanLabel     = fmtLoanFull(sel);
  const selfPct       = sel.self_ratio != null ? `${Math.round(sel.self_ratio * 100)}%` : '—';
  const netValue      = sel.net_value ?? result.objective_value;
  const lifetimeSav   = sel.lifetime_savings;
  const hasLoan       = (sel.loan_term_years ?? 0) > 0;

  return (
    <div className="solar-results">
      {/* System summary */}
      <div className="solar-results__summary">
        <div className="solar-results__summary-title">BEST SYSTEM FOUND</div>
        <div className="solar-results__stats">
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Panels</span>
            <strong className="solar-results__stat-value">{result.n_panels}</strong>
          </div>
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Efficiency</span>
            <strong className="solar-results__stat-value">{fmt(sel.efficiency, 0)}%</strong>
          </div>
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Battery</span>
            <strong className="solar-results__stat-value">{batteryLabel}</strong>
          </div>
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Self-consumption</span>
            <strong className="solar-results__stat-value">{selfPct}</strong>
          </div>
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Financing</span>
            <strong className="solar-results__stat-value">{loanLabel}</strong>
          </div>
          <div className="solar-results__stat">
            <span className="solar-results__stat-label">Sun hours</span>
            <strong className="solar-results__stat-value">{result.sunlight_hours_used} h/day</strong>
          </div>
        </div>
      </div>

      {/* Financial summary */}
      <div className="solar-results__financials">
        <div className="solar-results__fin-title">FINANCIAL SUMMARY</div>
        <div className="solar-results__fin-grid">
          <div className="solar-results__fin-item">
            <span className="solar-results__fin-label">System cost</span>
            <strong className="solar-results__fin-value">{fmtMoney(result.system_cost)}</strong>
          </div>
          {sel.monthly_payment > 0 && (
            <div className="solar-results__fin-item">
              <span className="solar-results__fin-label">Monthly payment</span>
              <strong className="solar-results__fin-value">{fmtMoney(sel.monthly_payment)}/mo</strong>
            </div>
          )}
          <div className="solar-results__fin-item">
            <span className="solar-results__fin-label">Annual savings</span>
            <strong className="solar-results__fin-value solar-results__fin-value--positive">
              {fmtMoney(result.annual_savings)}/yr
            </strong>
          </div>
          <div className="solar-results__fin-item">
            <span className="solar-results__fin-label">Payback period</span>
            <strong className="solar-results__fin-value">
              {result.payback_years != null ? `${result.payback_years} yr` : '—'}
            </strong>
          </div>
          <div className="solar-results__fin-item">
            <span className="solar-results__fin-label">Lifetime savings</span>
            <strong className="solar-results__fin-value solar-results__fin-value--positive">
              {fmtMoney(lifetimeSav)}
            </strong>
          </div>
          <div className="solar-results__fin-item">
            <span className="solar-results__fin-label">Net lifetime value</span>
            <strong className="solar-results__fin-value solar-results__fin-value--positive">
              {fmtMoney(netValue)}
            </strong>
          </div>
        </div>
      </div>

      {/* Cumulative savings chart */}
      <SavingsChart
        sel={sel}
        lifetime={result.system_lifetime ?? 25}
        annualSavings={result.annual_savings}
        systemCost={result.system_cost}
      />

      {/* Loan amortization toggle */}
      {hasLoan && (
        <button
          className="solar-btn solar-btn--secondary solar-amort__toggle"
          onClick={() => setShowAmort(v => !v)}
        >
          {showAmort ? '▲ Hide' : '▼ Show'} year-by-year amortization
        </button>
      )}

      {hasLoan && showAmort && (
        <AmortizationTable
          sel={sel}
          lifetime={result.system_lifetime ?? 25}
          annualSavings={result.annual_savings}
          systemCost={result.system_cost}
        />
      )}

      {/* Azimuth warning */}
      {result.azimuth_gain_pct > 0 && (
        <div className="solar-results__azimuth-warn">
          <span className="solar-results__azimuth-icon">↻</span>
          <span>
            Rotating panels to face <strong>{result.optimal_azimuth}</strong> would
            improve annual yield by <strong>{result.azimuth_gain_pct}%</strong>.
          </span>
        </div>
      )}

      {/* Winner config table */}
      {result.selections?.length > 0 && (
        <div className="solar-results__table-section">
          <div className="solar-results__table-title">
            SELECTED CONFIGURATION
            <span className="solar-results__table-sub">
              {' '}— evaluated {result.total_generated.toLocaleString()} combinations
            </span>
          </div>
          <div className="solar-results__table-scroll">
            <table className="solar-results__table">
              <thead>
                <tr>
                  <th>Eff (%)</th>
                  <th>$/W</th>
                  <th>Degr (%/yr)</th>
                  <th>Battery</th>
                  <th>Financing</th>
                  <th>System cost</th>
                  <th>Monthly</th>
                  <th>ROI</th>
                </tr>
              </thead>
              <tbody>
                {result.selections.map((s, i) => (
                  <tr key={s.id ?? i}>
                    <td>{fmt(s.efficiency, 0)}</td>
                    <td>{fmt(s.cost_per_watt, 3)}</td>
                    <td>{fmt(s.degradation_rate, 2)}</td>
                    <td>{s.battery_kwh > 0 ? `${s.battery_kwh} kWh` : 'None'}</td>
                    <td>{fmtLoan(s)}</td>
                    <td>{fmtMoney(s.system_cost)}</td>
                    <td>{s.monthly_payment > 0 ? fmtMoney(s.monthly_payment) + '/mo' : '—'}</td>
                    <td>{fmt(s.roi, 2)}×</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Runner-up alternatives */}
      <AlternativesSection alternatives={result.alternatives} />
    </div>
  );
}
