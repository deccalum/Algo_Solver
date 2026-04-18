import { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Icon } from '../../components/shared/Icon';
import { getSolves, streamSimulate } from '../../api/client';
import '../../styles/simulation-page.css';

const SCENARIO_HORIZONS = {
  '30-day forecast': 30,
  '60-day forecast': 60,
  '90-day forecast': 90,
  'stress test':     30,
};

const SCENARIO_STRESS = 'stress test';

// ── Small reusable SVG line chart ─────────────────────────────────────────────
function LineChart({ data, color = '#5b35d5', label, unit = '', height = 100 }) {
  if (!data || data.length < 2) {
    return (
      <div className="sim-chart__empty">No data yet</div>
    );
  }
  const W = 600;
  const H = height;
  const pad = { top: 6, right: 8, bottom: 18, left: 36 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;

  const minVal = Math.min(...data);
  const maxVal = Math.max(...data);
  const range  = maxVal - minVal || 1;

  const toX = i  => pad.left + (i / (data.length - 1)) * innerW;
  const toY = v  => pad.top  + innerH - ((v - minVal) / range) * innerH;

  const pts = data.map((v, i) => `${toX(i).toFixed(1)},${toY(v).toFixed(1)}`).join(' ');

  // Y-axis ticks (3)
  const ticks = [minVal, (minVal + maxVal) / 2, maxVal];

  return (
    <svg
      className="sim-chart__svg"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      style={{ height }}
    >
      {/* Grid lines + Y labels */}
      {ticks.map((v, i) => {
        const y = toY(v);
        return (
          <g key={i}>
            <line x1={pad.left} y1={y} x2={W - pad.right} y2={y}
              stroke="rgba(148,163,184,0.25)" strokeWidth="1" />
            <text x={pad.left - 4} y={y + 3.5} textAnchor="end"
              fontSize="9" fill="#94a3b8">
              {v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0)}
            </text>
          </g>
        );
      })}

      {/* Area fill */}
      <polyline
        points={`${pts} ${toX(data.length - 1).toFixed(1)},${(H - pad.bottom + 1).toFixed(1)} ${toX(0).toFixed(1)},${(H - pad.bottom + 1).toFixed(1)}`}
        fill={color}
        fillOpacity="0.08"
        stroke="none"
      />

      {/* Line */}
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" />

      {/* X axis label */}
      <text x={W / 2} y={H - 2} textAnchor="middle" fontSize="9" fill="#94a3b8">
        {label}
      </text>
    </svg>
  );
}

// ── Summary stats card ────────────────────────────────────────────────────────
function SummaryStats({ days, timeHorizon }) {
  if (!days || days.length === 0) return null;

  const totalSold     = days.reduce(
    (s, d) => s + Object.values(d.units_sold).reduce((a, b) => a + b, 0), 0
  );
  const reorderCount  = days.filter(d => d.action.startsWith('BUY')).length;
  const stockoutDays  = days.filter(d => d.log_level === 'warn').length;
  const fillRate      = (((days.length - stockoutDays) / days.length) * 100).toFixed(1);

  return (
    <div className="sim-summary">
      <div className="sim-summary__title">SIMULATION SUMMARY</div>
      <div className="sim-summary__grid">
        <div className="sim-summary__stat">
          <span className="sim-summary__label">Total units sold</span>
          <strong className="sim-summary__value">{totalSold.toLocaleString()}</strong>
        </div>
        <div className="sim-summary__stat">
          <span className="sim-summary__label">Reorders placed</span>
          <strong className="sim-summary__value">{reorderCount}</strong>
        </div>
        <div className="sim-summary__stat">
          <span className="sim-summary__label">Stockout days</span>
          <strong className={`sim-summary__value ${stockoutDays > 0 ? 'sim-summary__value--warn' : 'sim-summary__value--ok'}`}>
            {stockoutDays}
          </strong>
        </div>
        <div className="sim-summary__stat">
          <span className="sim-summary__label">Avg fill rate</span>
          <strong className={`sim-summary__value ${parseFloat(fillRate) >= 95 ? 'sim-summary__value--ok' : 'sim-summary__value--warn'}`}>
            {fillRate}%
          </strong>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────
function SliderField({ label, value, unit, accentColor, onChange }) {
  return (
    <div className="sim-page__slider">
      <div className="sim-page__slider-header">
        <span className="sim-page__slider-label">{label}</span>
        <span
          className="sim-page__slider-value"
          style={{ color: accentColor || 'var(--color-surface-tint)' }}
        >
          {value}{unit}
        </span>
      </div>
      <input
        type="range" min="0" max="100" step="1"
        className="sim-page__slider-input"
        style={{ accentColor: accentColor || '#4d44e3' }}
        defaultValue={50}
        onChange={onChange}
      />
    </div>
  );
}

function MetricCard({ label, value, unit, badge, badgeClass, bar, barFillClass }) {
  return (
    <div className="sim-page__metric">
      <span className="sim-page__metric-label">{label}</span>
      <div className="sim-page__metric-row">
        <span className="sim-page__metric-value">
          {value}{unit && <span className="sim-page__metric-unit">{unit}</span>}
        </span>
        {badge && (
          <span className={`sim-page__metric-badge ${badgeClass || ''}`}>{badge}</span>
        )}
      </div>
      {bar != null && (
        <div className="sim-page__metric-bar-track">
          <div
            className={`sim-page__metric-bar-fill ${barFillClass || ''}`}
            style={{ width: `${bar}%` }}
          />
        </div>
      )}
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function stockoutCount(days) {
  return days.filter(d => d.log_level === 'warn').length;
}

function stockoutPct(days) {
  if (!days || days.length === 0) return 0;
  return ((stockoutCount(days) / days.length) * 100).toFixed(1);
}

function avgDailySold(days) {
  if (!days || days.length === 0) return 0;
  const total = days.reduce(
    (sum, d) => sum + Object.values(d.units_sold).reduce((a, b) => a + b, 0),
    0
  );
  return (total / days.length).toFixed(0);
}

// ── Page ──────────────────────────────────────────────────────────────────────
export function SimulationPage() {
  // Persisted sim state lives in AppShell context so navigation doesn't reset it
  const { sessionCtx, setSessionCtx } = useOutletContext();

  const logs        = sessionCtx.simLogs    ?? [];
  const days        = sessionCtx.simDays    ?? [];
  const ledgerRows  = sessionCtx.simLedger  ?? [];
  const timeHorizon = sessionCtx.simHorizon ?? null;

  function setLogs(updater) {
    setSessionCtx(prev => ({ ...prev, simLogs: typeof updater === 'function' ? updater(prev.simLogs ?? []) : updater }));
  }
  function setDays(updater) {
    setSessionCtx(prev => ({ ...prev, simDays: typeof updater === 'function' ? updater(prev.simDays ?? []) : updater }));
  }
  function setLedgerRows(updater) {
    setSessionCtx(prev => ({ ...prev, simLedger: typeof updater === 'function' ? updater(prev.simLedger ?? []) : updater }));
  }
  function setTimeHorizon(v) {
    setSessionCtx(prev => ({ ...prev, simHorizon: v }));
  }

  const [running,  setRunning]  = useState(false);
  const [scenario, setScenario] = useState('30-day forecast');
  const [solves,   setSolves]   = useState([]);
  const [solveId,  setSolveId]  = useState(null);
  const [error,    setError]    = useState(null);

  const consoleRef = useRef(null);
  const abortRef   = useRef(null);

  useEffect(() => {
    getSolves(20, 0)
      .then(runs => {
        setSolves(runs);
        if (runs.length > 0 && !solveId) setSolveId(runs[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  async function handleRunStop() {
    if (running) {
      abortRef.current?.abort();
      setRunning(false);
      return;
    }
    if (!solveId) {
      setError('No solve run selected — run a solve first.');
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;

    setRunning(true);
    setError(null);
    setLogs([]);
    setLedgerRows([]);
    setDays([]);
    setTimeHorizon(null);

    const isStress = scenario === SCENARIO_STRESS;
    try {
      await streamSimulate(
        {
          solve_id: solveId,
          config: {
            time_horizon:      SCENARIO_HORIZONS[scenario] ?? 30,
            space_capacity:    isStress ? 200.0 : 500.0,
            space_buffer:      isStress ? 0.30  : 0.15,
            lead_time:         isStress ? 7     : 3,
            budget:            50_000,
            reorder_threshold: 0.25,
          },
        },
        (msg) => {
          if (msg.type === 'meta') {
            setTimeHorizon(msg.time_horizon);
          } else if (msg.type === 'day') {
            const snap = msg;
            setDays(prev => [...prev, snap]);
            setLogs(prev => [...prev, {
              day:   `Day ${String(snap.day).padStart(2, '0')}`,
              level: snap.log_level,
              text:  snap.log_text,
            }]);
            setLedgerRows(prev => {
              const opening = Object.values(snap.stock).reduce((a, b) => a + b, 0)
                            + Object.values(snap.units_sold).reduce((a, b) => a + b, 0)
                            - Object.values(snap.units_received).reduce((a, b) => a + b, 0);
              const sales   = Object.values(snap.units_sold).reduce((a, b) => a + b, 0);
              const closing = Object.values(snap.stock).reduce((a, b) => a + b, 0);
              const isPending = Object.keys(snap.units_ordered).length > 0;
              return [...prev, {
                day:     `D-${String(snap.day).padStart(2, '0')}`,
                opening: Math.max(0, opening),
                sales,
                closing,
                action:  snap.action,
                spike:   snap.log_level === 'warn',
                pending: isPending && snap.action.startsWith('BUY'),
                space:   snap.space_used.toFixed(1),
              }];
            });
          }
        },
        controller.signal,
      );
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  const soPCT   = days.length > 0 ? stockoutPct(days)   : '—';
  const avgSold = days.length > 0 ? avgDailySold(days)   : '—';

  // Derive chart data from days
  const spaceData = days.map(d => d.space_used);
  const stockData = days.map(d => Object.values(d.stock).reduce((a, b) => a + b, 0));

  return (
    <div>
      {/* Action Strip */}
      <div className="sim-page__action-strip">
        <div className="sim-page__action-left">
          <div className="sim-page__objective">
            <span className="sim-page__objective-label">Objective:</span>
            <span className="sim-page__objective-badge">MINIMIZE STOCKOUTS</span>
          </div>
          <div className="sim-page__status">
            <span className={`sim-page__status-dot ${running ? 'sim-page__status-dot--running' : 'sim-page__status-dot--paused'}`} />
            <span className="sim-page__status-text">
              {running
                ? `SIMULATING… day ${days.length}${timeHorizon ? ` / ${timeHorizon}` : ''}`
                : days.length > 0 ? `DONE — ${days.length} days` : 'READY'}
            </span>
          </div>
          <select
            className="sim-page__scenario-select"
            value={scenario}
            onChange={e => setScenario(e.target.value)}
          >
            {Object.keys(SCENARIO_HORIZONS).map(s => (
              <option key={s}>{s}</option>
            ))}
          </select>
          {solves.length > 0 && (
            <select
              className="sim-page__scenario-select"
              value={solveId || ''}
              onChange={e => setSolveId(e.target.value)}
            >
              {solves.map(s => (
                <option key={s.id} value={s.id}>
                  Solve {s.id.slice(0, 8)}… ({s.selected_count} items)
                </option>
              ))}
            </select>
          )}
        </div>
        <button
          className={`sim-page__run-btn ${running ? 'sim-page__run-btn--stop' : 'sim-page__run-btn--run'}`}
          onClick={handleRunStop}
        >
          <Icon name={running ? 'stop_circle' : 'play_circle'} className="sim-page__run-btn-icon" />
          {running ? 'STOP' : 'RUN SIMULATION'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '8px 16px', background: '#fef2f2', color: '#b91c1c', fontSize: 12, fontFamily: 'var(--font-mono)' }}>
          {error}
        </div>
      )}

      {/* Main layout */}
      <div className="sim-page__grid">

        {/* Left column */}
        <div className="sim-page__left">

          {/* Time-series charts */}
          <section className="sim-page__card">
            <div className="sim-page__chart-header">
              <h2 className="sim-page__section-heading">
                {days.length > 0 ? 'Simulation Time-Series' : 'Daily Projection Analysis'}
              </h2>
              {days.length > 0 ? (
                <div className="sim-page__chart-legend">
                  <span className="sim-page__legend-item">
                    <span className="sim-page__legend-line sim-page__legend-line--cyan" /> Space Used (m³)
                  </span>
                  <span className="sim-page__legend-item">
                    <span className="sim-page__legend-line sim-page__legend-line--accent" /> Total Stock (units)
                  </span>
                </div>
              ) : (
                <div className="sim-page__chart-legend">
                  <span className="sim-page__legend-item">
                    <span className="sim-page__legend-line sim-page__legend-line--cyan" /> Projected Sales
                  </span>
                  <span className="sim-page__legend-item">
                    <span className="sim-page__legend-line sim-page__legend-line--accent" /> Inventory Level
                  </span>
                  <span className="sim-page__legend-item">
                    <span className="sim-page__legend-line sim-page__legend-line--dashed" /> Safety Stock
                  </span>
                </div>
              )}
            </div>

            {days.length > 0 ? (
              <div className="sim-charts">
                <div className="sim-charts__row">
                  <div className="sim-charts__label">Space utilisation</div>
                  <LineChart data={spaceData} color="#06b6d4" label="Days" unit=" m³" height={90} />
                </div>
                <div className="sim-charts__row">
                  <div className="sim-charts__label">Total stock</div>
                  <LineChart data={stockData} color="#5b35d5" label="Days" unit=" units" height={90} />
                </div>
              </div>
            ) : (
              <div className="sim-page__chart-area">
                <svg className="sim-page__chart-svg" preserveAspectRatio="none" viewBox="0 0 1100 300">
                  <line x1="0" y1="220" x2="1100" y2="220" stroke="#94a3b8" strokeDasharray="6 4" strokeWidth="1" />
                  <path d="M0 250 Q100 240 200 260 T400 230 T600 270 T800 220 T1100 250"
                    fill="none" stroke="#06b6d4" strokeWidth="2" />
                  <path d="M0 250 Q100 240 200 260 T400 230 T600 270 T800 220 T1100 250 L1100 300 L0 300 Z"
                    fill="rgba(6,182,212,0.06)" />
                  <path d="M0 100 L100 80 L200 150 L300 220 L305 50 L500 120 L700 180 L705 40 L900 110 L1100 160"
                    fill="none" stroke="#5b35d5" strokeWidth="2.5" />
                  <circle cx="305" cy="50" r="5" fill="#5b35d5" />
                  <circle cx="705" cy="40" r="5" fill="#5b35d5" />
                </svg>
                <div className="sim-page__chart-y-axis">
                  <span>500</span><span>400</span><span>300</span><span>200</span><span>100</span><span>0</span>
                </div>
              </div>
            )}
            {!days.length && (
              <div className="sim-page__chart-x-axis">
                <span>Day 01</span><span>Day 07</span><span>Day 14</span><span>Day 21</span><span>Day 30</span>
              </div>
            )}
          </section>

          {/* Simulation controls — cosmetic sliders */}
          <div className="sim-page__controls-grid">
            <section className="sim-page__card">
              <div className="sim-page__control-header">
                <Icon name="casino" className="sim-page__control-icon--accent" />
                <h3 className="sim-page__section-heading">Monte Carlo Shocks</h3>
              </div>
              <div className="sim-page__control-sliders">
                <SliderField label="Lead Time Variance" value="±2.4" unit="d" />
                <SliderField label="Demand Spike Prob." value="12" unit="%" />
                <SliderField label="Supplier Reliability" value="94.2" unit="%" />
              </div>
            </section>

            <section className="sim-page__card">
              <div className="sim-page__control-header">
                <Icon name="settings_input_component" className="sim-page__control-icon--cyan" />
                <h3 className="sim-page__section-heading">Auto-Solve Triggers</h3>
              </div>
              <div className="sim-page__control-sliders">
                <SliderField label="Re-order Threshold" value="25" unit="%" accentColor="#06b6d4" />
                <SliderField label="Buffer Safety Factor" value="1.5" unit="x" accentColor="#06b6d4" />
                <SliderField label="Cost-to-Serve Limit" value="$45.00" unit="/u" accentColor="#06b6d4" />
              </div>
            </section>
          </div>

          {/* Summary stats — shown after run */}
          {!running && days.length > 0 && (
            <SummaryStats days={days} timeHorizon={timeHorizon} />
          )}

          {/* Daily Ledger — live data when simulation has run */}
          <section className="sim-page__card sim-page__card--no-pad sim-page__ledger">
            <div className="sim-page__ledger-header">
              <h2 className="sim-page__section-heading">
                {days.length > 0
                  ? `Simulation Ledger — ${timeHorizon ?? days.length}-day run`
                  : 'Simulation Ledger — run to populate'}
              </h2>
            </div>
            <div className="sim-page__ledger-scroll">
              <table className="sim-page__ledger-table">
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>Opening Inv</th>
                    <th>Est. Sales</th>
                    <th>Solver Action</th>
                    <th>Closing Inv</th>
                    <th>Space Used</th>
                  </tr>
                </thead>
                <tbody>
                  {ledgerRows.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8', fontSize: 11, padding: '16px 0' }}>
                        No data — click RUN SIMULATION
                      </td>
                    </tr>
                  )}
                  {ledgerRows.map(row => (
                    <tr key={row.day} className={row.spike ? 'sim-page__ledger-row--spike' : ''}>
                      <td className="sim-page__ledger-day">{row.day}</td>
                      <td className="sim-page__ledger-dim">{row.opening}</td>
                      <td className="sim-page__ledger-dim">
                        {row.sales}
                        {row.spike && (
                          <span className="sim-page__ledger-spike-badge">STOCKOUT</span>
                        )}
                      </td>
                      <td>
                        {row.action === 'HOLD'
                          ? <span className="sim-page__ledger-action--hold">HOLD</span>
                          : row.pending
                            ? <span className="sim-page__ledger-action--buy">{row.action}</span>
                            : <span className="sim-page__ledger-action--hold">{row.action}</span>
                        }
                      </td>
                      <td className="sim-page__ledger-dim">{row.closing}</td>
                      <td className="sim-page__ledger-margin">{row.space} m³</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Right column */}
        <aside className="sim-page__right">

          {/* Console — live logs when simulation has run */}
          <section className="sim-page__console">
            <div className="sim-page__console-bar">
              <div className="sim-page__console-bar-left">
                <div className="sim-page__console-dots">
                  <div className="sim-page__console-dot sim-page__console-dot--red" />
                  <div className="sim-page__console-dot sim-page__console-dot--yellow" />
                  <div className="sim-page__console-dot sim-page__console-dot--green" />
                </div>
                <span className="sim-page__console-title">SYSTEM_LOG</span>
              </div>
              <span className="sim-page__console-status">
                {running ? 'Live' : logs.length > 0 ? `${logs.length} entries` : 'Ready'}
              </span>
            </div>
            <div className="sim-page__console-body custom-scrollbar" ref={consoleRef}>
              {logs.length === 0 && (
                <p style={{ color: '#475569', fontSize: 11 }}>Waiting for simulation…</p>
              )}
              {logs.map((log, i) => (
                <p key={i}>
                  <span className="sim-page__log-timestamp">[{log.day}]</span>{' '}
                  <span className={`sim-page__log--${log.level}`}>{log.text}</span>
                </p>
              ))}
              {running && <p className="sim-page__console-cursor">_</p>}
            </div>
          </section>

          {/* Metrics — live when simulation has run, cosmetic otherwise */}
          <div className="sim-page__metrics">
            <MetricCard
              label="Stockout Days"
              value={soPCT}
              unit={days.length > 0 ? '%' : ''}
              badge={days.length > 0 ? (parseFloat(soPCT) < 5 ? 'LOW RISK' : 'HIGH RISK') : '—'}
              badgeClass={days.length > 0 && parseFloat(soPCT) < 5
                ? 'sim-page__metric-badge--emerald'
                : 'sim-page__metric-badge--muted'}
              bar={days.length > 0 ? Math.min(parseFloat(soPCT) * 2, 100) : null}
              barFillClass="sim-page__metric-bar-fill--red"
            />
            <MetricCard
              label="Avg Daily Sales"
              value={avgSold}
              unit={days.length > 0 ? ' units' : ''}
              badge={days.length > 0 ? 'LIVE' : '—'}
              badgeClass="sim-page__metric-badge--muted"
            />
            <MetricCard
              label="Inventory Turns"
              value={days.length > 0 ? ((timeHorizon ?? days.length) / 30 * 8.4).toFixed(1) : '—'}
              unit={days.length > 0 ? 'x' : ''}
              badge={days.length > 0 ? 'EST.' : '—'}
              badgeClass="sim-page__metric-badge--accent"
            />
            <div className="sim-page__metric">
              <span className="sim-page__metric-label">Solver Latency</span>
              <div className="sim-page__metric-row">
                <span className="sim-page__metric-value">
                  12<span className="sim-page__metric-unit">ms</span>
                </span>
                <div className="sim-page__latency-bars">
                  {[10, 14, 8, 18, 12, 16, 12].map((h, i) => (
                    <span key={i} className="sim-page__latency-bar" style={{ height: `${h}px` }} />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Region Monitor — cosmetic */}
          <div className="sim-page__region">
            <div className="sim-page__region-glow" />
            <div className="sim-page__region-grid" />
            <div className="sim-page__region-info">
              <span className="sim-page__region-label">Region Monitor</span>
              <p className="sim-page__region-name">North Atlantic Corridor</p>
            </div>
            <div className="sim-page__region-live">
              <span className="sim-page__region-live-dot" />
              LIVE
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
