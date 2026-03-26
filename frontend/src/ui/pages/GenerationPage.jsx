import { useEffect, useMemo, useState } from "react";
import {
  Check,
  Copy,
  DollarSign,
  Download,
  FolderOpen,
  Grid2x2,
  Plus,
  Ruler,
  SlidersHorizontal,
  Trash2,
  Upload,
  Play,
  AlertCircle,
  CheckCircle,
  Loader,
} from "lucide-react";
import { fetchGenerationConfig, generateCatalog, checkApiStatus } from "../../api/configApi";
import styles from "../styles/GenerationDashboard.module.css";

const optimizationModes = [
  "Balanced Algorithm",
  "Maximum Density",
  "Value Skew",
];

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function formatCompact(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  if (Math.abs(number) >= 1_000_000) return `$${(number / 1_000_000).toFixed(1)}M`;
  if (Math.abs(number) >= 1_000) return `${(number / 1_000).toFixed(1)}k`;
  return number.toLocaleString("en-US");
}

function formatCurrency(value) {
  return `$${Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatSize(value) {
  return `${Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}m²`;
}

function buildBarSeries(priceMin, priceMax, budget, mode) {
  const span = Math.max(priceMax - priceMin, 1);
  const budgetFactor = clamp(Number(budget) / 100000, 0.4, 2.4);
  const modeFactor = mode === "Maximum Density" ? 1.2 : mode === "Value Skew" ? 0.9 : 1;

  return Array.from({ length: 10 }, (_, index) => {
    const t = index / 9;
    const center = mode === "Value Skew" ? 0.62 : mode === "Maximum Density" ? 0.48 : 0.38;
    const width = clamp((span / 1000) * 0.18 + 0.16, 0.16, 0.34);
    const gaussian = Math.exp(-((t - center) ** 2) / width);
    const value = clamp((gaussian * 78 + budgetFactor * 12 + index * modeFactor * 0.8), 4, 100);
    return Math.round(value);
  });
}

function buildLinePath(sizeMin, sizeMax, spanShare, mode) {
  const spread = Math.max(sizeMax - sizeMin, 1);
  const peak = clamp(18 + spanShare * 0.55, 20, 72);
  const valley = mode === "Maximum Density" ? 72 : mode === "Value Skew" ? 82 : 88;
  const end = clamp(50 + spread * 0.25, 40, 92);

  return `M0 ${end} Q 50 12, 100 ${peak} T 200 ${valley} T 300 8 T 400 ${end - 8}`;
}

function MetricCard({
  label,
  accent,
  value,
  suffix,
  min,
  max,
  fill,
}) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricHeader}>
        <span className={accent === "cyan" ? styles.metricLabelCyan : styles.metricLabel}>{label}</span>
        <div className={styles.metricValueWrap}>
          <span className={styles.metricValue}>{value}</span>
          {suffix && <span className={styles.metricUnit}>{suffix}</span>}
        </div>
      </div>
      <div className={styles.progressTrack}>
        <div
          className={accent === "cyan" ? styles.progressFillCyan : styles.progressFillViolet}
          style={{ width: `${fill}%` }}
        />
      </div>
      <div className={styles.metricBounds}>
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

function RangeCard({
  accent,
  icon,
  title,
  subtitle,
  left,
  right,
  minLabel,
  minValue,
  maxLabel,
  maxValue,
}) {
  return (
    <section className={styles.rangeCard}>
      <div className={styles.rangeHeader}>
        <div className={accent === "cyan" ? styles.rangeIconCyan : styles.rangeIconViolet}>{icon}</div>
        <div>
          <h4>{title}</h4>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className={styles.sliderShell}>
        <div className={styles.sliderTrack}>
          <div
            className={accent === "cyan" ? styles.sliderActiveCyan : styles.sliderActiveViolet}
            style={{ left: `${left}%`, right: `${right}%` }}
          />
          <span className={styles.sliderKnob} style={{ left: `${left}%` }} />
          <span className={styles.sliderKnob} style={{ right: `${right}%` }} />
        </div>
      </div>
      <div className={styles.rangeValues}>
        <div className={styles.rangeValueCard}>
          <span>{minLabel}</span>
          <strong>{minValue}</strong>
        </div>
        <div className={styles.rangeValueCard}>
          <span>{maxLabel}</span>
          <strong>{maxValue}</strong>
        </div>
      </div>
    </section>
  );
}

export default function GenerationPage() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingMetric, setEditingMetric] = useState(null);
  const [activeZoneTab, setActiveZoneTab] = useState("price");
  const [activeMode, setActiveMode] = useState("Balanced Algorithm");
  const [spanShare, setSpanShare] = useState(64);
  const [priceLeft] = useState(15);
  const [priceRight] = useState(25);
  const [sizeLeft] = useState(30);
  const [sizeRight] = useState(10);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState(null);
  const [generationError, setGenerationError] = useState(null);
  const [apiConnected, setApiConnected] = useState(false);
  const [lastStatusCheck, setLastStatusCheck] = useState(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const data = await fetchGenerationConfig();
        setConfig(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    loadConfig();
  }, []);

  // Check API connectivity periodically
  useEffect(() => {
    const checkConnectivity = async () => {
      try {
        await checkApiStatus();
        setApiConnected(true);
        setLastStatusCheck(new Date());
      } catch (err) {
        setApiConnected(false);
        setLastStatusCheck(new Date());
      }
    };

    checkConnectivity();
    const interval = setInterval(checkConnectivity, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerationError(null);
    setGenerationResult(null);

    try {
      const result = await generateCatalog(1000); // Generate 1000 products
      setGenerationResult(result);
    } catch (err) {
      setGenerationError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  // All hooks must be called before any conditional returns
  const budget = config?.generation?.budget || 0;
  const space = config?.generation?.space || 0;

  const priceRange = useMemo(() => {
    if (!config?.generation) return [1, 10000];
    const min = config.generation.min_price || 1;
    const max = config.generation.max_price || 10000;
    return [min, max];
  }, [config?.generation?.min_price, config?.generation?.max_price]);

  const sizeRange = useMemo(() => {
    if (!config?.generation) return [0.1, 100000];
    const min = config.generation.min_size || 0.1;
    const max = config.generation.max_size || 100000;
    return [min, max];
  }, [config?.generation?.min_size, config?.generation?.max_size]);

  const barSeries = useMemo(
    () => buildBarSeries(priceRange[0], priceRange[1], budget, activeMode),
    [activeMode, budget, priceRange],
  );

  const peakIndex = barSeries.indexOf(Math.max(...barSeries));
  const linePath = useMemo(
    () => buildLinePath(sizeRange[0], sizeRange[1], spanShare, activeMode),
    [activeMode, sizeRange, spanShare],
  );

  const sigma = useMemo(() => {
    const spread = priceRange[1] - priceRange[0];
    return (spread / Math.max(budget || 1, 1) * 100).toFixed(2);
  }, [budget, priceRange]);

  const mu = useMemo(() => ((sizeRange[0] + sizeRange[1]) / 2).toFixed(1), [sizeRange]);

  const diagnostics = useMemo(
    () => [
      ["Zone Resolution", `${Math.round((priceRange[1] - priceRange[0]) / 12)} px/m`],
      ["Vector Bias", `${activeMode === "Value Skew" ? "+0.42%" : activeMode === "Maximum Density" ? "+0.25%" : "+0.12%"}`],
      ["Entropy Factor", spanShare > 72 ? "Aggressive" : spanShare < 38 ? "Conservative" : "Stable"],
    ],
    [activeMode, priceRange, spanShare],
  );

  const persistConfig = (nextBudget, nextSpace, nextMode = activeMode, nextSpanShare = spanShare) => {
    updateGenerationConfig({
      solver: {
        budget: nextBudget,
        space: nextSpace,
      },
      generation: {
        priceRange,
        sizeRange,
        mode: nextMode,
        spanShare: nextSpanShare,
      },
    });
  };

  if (loading) {
    return (
      <main className={styles.page}>
        <div className={styles.mainColumn}>
          <div className={styles.workspace}>
            <div className={styles.heroCompact}>
              <h2>Loading Configuration...</h2>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className={styles.page}>
        <div className={styles.mainColumn}>
          <div className={styles.workspace}>
            <div className={styles.heroCompact}>
              <h2>Error Loading Configuration</h2>
              <p>{error}</p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (!config) return null;

  return (
    <main className={styles.page}>
      <div className={styles.mainColumn}>


        <section className={styles.contentShell}>
          <aside className={styles.sideNav}>
            <button className={styles.sideNavActive} type="button">
              <Grid2x2 size={14} />
              Generation
            </button>
            <button className={styles.sideNavItem} type="button">
              <Copy size={14} />
              Solver
            </button>
            <button className={styles.sideNavItem} type="button">
              <Ruler size={14} />
              Database
            </button>
            <button className={styles.sideNavItem} type="button">
              <Trash2 size={14} />
              Empty
            </button>

            <div className={styles.profileCard}>
              <div className={styles.profileAvatar}>A</div>
              <div>
                <strong>Admin Operator</strong>
                <span>ID: 99283-SLV</span>
              </div>
            </div>
          </aside>

          <div className={styles.workspace}>
            <div className={styles.heroCompact}>
              <div>
                <h2>Algorithmic Engine</h2>
                <p>Generation Workspace // v4.0.1</p>
                <div className={styles.statusIndicators}>
                  <div className={styles.statusItem}>
                    {apiConnected ? (
                      <CheckCircle size={14} className={styles.statusSuccess} />
                    ) : (
                      <AlertCircle size={14} className={styles.statusError} />
                    )}
                    <span>API {apiConnected ? 'Connected' : 'Disconnected'}</span>
                    {lastStatusCheck && (
                      <small>Last check: {lastStatusCheck.toLocaleTimeString()}</small>
                    )}
                  </div>
                  {generationResult && (
                    <div className={styles.statusItem}>
                      <CheckCircle size={14} className={styles.statusSuccess} />
                      <span>{generationResult.generated_count} products generated</span>
                    </div>
                  )}
                  {generationError && (
                    <div className={styles.statusItem}>
                      <AlertCircle size={14} className={styles.statusError} />
                      <span>Generation failed: {generationError}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className={styles.heroButtonsCompact}>
                <button
                  className={styles.ghostButton}
                  type="button"
                  disabled={!apiConnected}
                >
                  <FolderOpen size={14} />
                  Load Project
                </button>
                <button
                  className={`${styles.primaryButton} ${generating ? styles.buttonLoading : ''}`}
                  type="button"
                  onClick={handleGenerate}
                  disabled={!apiConnected || generating}
                >
                  {generating ? (
                    <>
                      <Loader size={14} className={styles.spinning} />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Play size={14} />
                      Generate Catalog
                    </>
                  )}
                </button>
                <button className={styles.secondaryButton} type="button">
                  <Download size={14} />
                  Export Solver
                </button>
              </div>
            </div>

            <div className={styles.dashboardGridExact}>
              <div className={styles.metricColumn}>
                <MetricCard
                  label="Global Budget"
                  accent="violet"
                  value={formatCompact(budget)}
                  suffix=""
                  min="Min: $100k"
                  max="Max: $5.0M"
                  fill={clamp((budget / 5000000) * 100, 2, 100)}
                />
                <MetricCard
                  label="Space Capacity"
                  accent="cyan"
                  value={formatCompact(space)}
                  suffix=""
                  min="Min: 500 units"
                  max="Max: 20k units"
                  fill={clamp((space / 20000) * 100, 2, 100)}
                />
              </div>

              <section className={styles.chartPanelExact}>
                <div className={styles.panelHeaderExact}>
                  <div className={styles.panelTitleWrap}>
                    <span className={styles.panelMarker} />
                    <h3>Distribution Mapping</h3>
                  </div>
                  <div className={styles.panelActions}>
                    <button type="button" aria-label="Grid view">
                      <Grid2x2 size={14} />
                    </button>
                    <button type="button" aria-label="Copy view">
                      <Copy size={14} />
                    </button>
                  </div>
                </div>

                <div className={styles.chartGridExact}>
                  <div className={styles.chartCardCompact}>
                    <div className={styles.chartTitleRow}>
                      <span>Price Frequency</span>
                      <strong>σ {sigma}</strong>
                    </div>
                    <div className={styles.barChartExact}>
                      {barSeries.map((height, index) => (
                        <span
                          key={`${height}-${index}`}
                          className={index === peakIndex ? styles.barActive : styles.bar}
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>
                    <div className={styles.chartBaseLine} />
                  </div>

                  <div className={styles.chartCardCompact}>
                    <div className={styles.chartTitleRow}>
                      <span>Size Allocation</span>
                      <strong className={styles.cyanText}>μ {mu}</strong>
                    </div>
                    <div className={styles.lineChartWrapExact}>
                      <svg viewBox="0 0 400 100" className={styles.lineChart} preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="areaGradLive" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="#4cd7f6" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#4cd7f6" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <path d={`${linePath} L 400 100 L 0 100 Z`} fill="url(#areaGradLive)" />
                        <path d={linePath} fill="none" stroke="#4cd7f6" strokeWidth="2.5" />
                      </svg>
                    </div>
                    <div className={styles.chartBaseLine} />
                  </div>
                </div>
              </section>

              <div className={styles.rangeGrid}>
                <RangeCard
                  icon={<DollarSign size={16} />}
                  title="Price Range Threshold"
                  subtitle="Financial Bounds"
                  left={priceLeft}
                  right={priceRight}
                  minLabel="Min Price"
                  minValue={formatCurrency(priceRange[0])}
                  maxLabel="Max Price"
                  maxValue={formatCurrency(priceRange[1])}
                />
                <RangeCard
                  accent="cyan"
                  icon={<Ruler size={16} />}
                  title="Size Range Granularity"
                  subtitle="Geometric Scaling"
                  left={sizeLeft}
                  right={sizeRight}
                  minLabel="Min Size"
                  minValue={formatSize(sizeRange[0])}
                  maxLabel="Max Size"
                  maxValue={formatSize(sizeRange[1])}
                />
              </div>

              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <button
                    type="button"
                    className={activeZoneTab === "price" ? styles.zoneTabActive : styles.zoneTab}
                    onClick={() => setActiveZoneTab("price")}
                  >
                    Price Zones
                  </button>
                  <button
                    type="button"
                    className={activeZoneTab === "size" ? styles.zoneTabActive : styles.zoneTab}
                    onClick={() => setActiveZoneTab("size")}
                  >
                    Size Zones
                  </button>
                  <div className={styles.zoneSettings}>
                    <button type="button" aria-label="Zone settings">
                      <SlidersHorizontal size={14} />
                    </button>
                  </div>
                </div>

                <div className={styles.zoneContentExact}>
                  <div className={styles.zoneSectionCompact}>
                    <div className={styles.spanHeaderExact}>
                      <label htmlFor="spanShare">Span Share</label>
                      <strong>{spanShare}%</strong>
                    </div>
                    <input
                      id="spanShare"
                      className={styles.sliderInput}
                      type="range"
                      min="0"
                      max="100"
                      value={spanShare}
                      onChange={(event) => {
                        const next = Number(event.target.value);
                        setSpanShare(next);
                        persistConfig(budget, space, activeMode, next);
                      }}
                    />
                    <div className={styles.spanLabels}>
                      <span>Conservative</span>
                      <span>Aggressive</span>
                    </div>
                  </div>

                  <div className={styles.zoneSectionCompact}>
                    <label className={styles.sectionLabel}>Optimization Mode</label>
                    <div className={styles.modeList}>
                      {optimizationModes.map((mode) => {
                        const active = mode === activeMode;
                        return (
                          <button
                            key={mode}
                            type="button"
                            className={active ? styles.modeButtonActive : styles.modeButton}
                            onClick={() => {
                              setActiveMode(mode);
                              persistConfig(budget, space, mode, spanShare);
                            }}
                          >
                            <span>{mode}</span>
                            {active ? <Check size={14} /> : null}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className={styles.diagnosticsCardExact}>
                    {diagnostics.map(([label, value]) => (
                      <div key={label} className={styles.diagnosticRow}>
                        <span>{label}</span>
                        <strong>{value}</strong>
                      </div>
                    ))}
                    <button className={styles.secondaryButton} type="button">
                      <Copy size={14} />
                      Full Diagnostics
                    </button>
                  </div>
                </div>
              </section>

              {/* Demand Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Demand Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Base Demand</span>
                      <strong>{(config.demand?.base_demand || 0).toFixed(3)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Scale</span>
                      <strong>{formatCompact(config.demand?.price_scale || 0)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Size Scale</span>
                      <strong>{formatCompact(config.demand?.size_scale || 0)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Sensitivity</span>
                      <strong>{(config.demand?.price_sensitivity || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Size Sensitivity</span>
                      <strong>{(config.demand?.size_sensitivity || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Noise</span>
                      <strong>{(config.demand?.noise || 0).toFixed(3)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Demand Range</span>
                      <strong>{(config.demand?.min_demand || 0).toFixed(2)} - {(config.demand?.max_demand || 0).toFixed(2)}</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Markup Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Markup Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Base Rate</span>
                      <strong>{((config.markup?.base_rate || 0) * 100).toFixed(1)}%</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Scale</span>
                      <strong>{(config.markup?.price_scale || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Max Rate</span>
                      <strong>{((config.markup?.max_rate || 0) * 100).toFixed(1)}%</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Noise</span>
                      <strong>{(config.markup?.noise || 0).toFixed(3)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Divisor</span>
                      <strong>{config.markup?.price_divisor || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Rate Range</span>
                      <strong>{((config.markup?.min_rate || 0) * 100).toFixed(1)}% - {((config.markup?.max_rate_clamp || 0) * 100).toFixed(1)}%</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Transit Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Transit Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Min Capacity Epsilon</span>
                      <strong>{(config.transit?.min_capacity_epsilon || 0).toFixed(7)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Weight/Volume Ratio</span>
                      <strong>{config.transit?.weight_volume_ratio || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Origin</span>
                      <strong>{(config.transit?.origin || 0).toFixed(2)}</strong>
                    </div>
                  </div>
                  <div className={styles.zoneSectionCompact}>
                    <label className={styles.sectionLabel}>Transit Modes</label>
                    <div className={styles.diagnosticsCardExact}>
                      {config.transit?.courier && (
                        <div className={styles.diagnosticRow}>
                          <span>Courier</span>
                          <strong>Cap: {config.transit.courier.capacity}, Cost: ${config.transit.courier.base_cost}</strong>
                        </div>
                      )}
                      {config.transit?.pallet && (
                        <div className={styles.diagnosticRow}>
                          <span>Pallet</span>
                          <strong>Cap: {config.transit.pallet.capacity}, Cost: ${config.transit.pallet.base_cost}</strong>
                        </div>
                      )}
                      {config.transit?.container && (
                        <div className={styles.diagnosticRow}>
                          <span>Container</span>
                          <strong>Cap: {config.transit.container.capacity}, Cost: ${config.transit.container.base_cost}</strong>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </section>

              {/* Logistics Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Logistics Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Min Size Log</span>
                      <strong>{config.logistics?.min_size_log || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Penalty Factor</span>
                      <strong>{(config.logistics?.penalty_factor || 0).toFixed(3)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Max Difficulty</span>
                      <strong>{(config.logistics?.max_difficulty || 0).toFixed(3)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Optimal</span>
                      <strong>{config.logistics?.optimal || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Base Cost</span>
                      <strong>{config.logistics?.base_cost || 0}</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Stock Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Stock Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Base Stock</span>
                      <strong>{formatCompact(config.stock?.base_stock || 0)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Stock</span>
                      <strong>{config.stock?.min_stock || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Noise</span>
                      <strong>{(config.stock?.noise || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Infinite Stock Value</span>
                      <strong>{config.stock?.infinite_stock_value || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Infinite Chance Base</span>
                      <strong>{(config.stock?.infinite_chance_base || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Infinite Decay Scale</span>
                      <strong>{config.stock?.infinite_decay_scale || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Infinite Decay Size</span>
                      <strong>{config.stock?.infinite_decay_size || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Scale</span>
                      <strong>{formatCompact(config.stock?.price_scale || 0)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Size Scale</span>
                      <strong>{formatCompact(config.stock?.size_scale || 0)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Price Sensitivity</span>
                      <strong>{(config.stock?.price_sensitivity || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Size Sensitivity</span>
                      <strong>{(config.stock?.size_sensitivity || 0).toFixed(2)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Price Norm</span>
                      <strong>{config.stock?.min_price_norm || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Size Norm</span>
                      <strong>{config.stock?.min_size_norm || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Scale</span>
                      <strong>{config.stock?.min_scale || 0}</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Guardrails Configuration */}
              <section className={styles.zonePanelExact}>
                <div className={styles.zoneTabsExact}>
                  <h3>Guardrails Configuration</h3>
                </div>
                <div className={styles.zoneContentExact}>
                  <div className={styles.diagnosticsCardExact}>
                    <div className={styles.diagnosticRow}>
                      <span>Min Span</span>
                      <strong>{config.guardrails?.min_span || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Step</span>
                      <strong>{config.guardrails?.min_step || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Resolution</span>
                      <strong>{config.guardrails?.min_resolution || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Bias</span>
                      <strong>{(config.guardrails?.min_bias || 0).toFixed(4)}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Safe Start</span>
                      <strong>{config.guardrails?.min_safe_start || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Min Count</span>
                      <strong>{config.guardrails?.min_count || 0}</strong>
                    </div>
                    <div className={styles.diagnosticRow}>
                      <span>Round Min</span>
                      <strong>{config.guardrails?.round_min || 0}</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Generation Results */}
              {generationResult && (
                <section className={styles.zonePanelExact}>
                  <div className={styles.zoneTabsExact}>
                    <h3>Generation Results</h3>
                  </div>
                  <div className={styles.zoneContentExact}>
                    <div className={styles.diagnosticsCardExact}>
                      <div className={styles.diagnosticRow}>
                        <span>Products Generated</span>
                        <strong>{generationResult.generated_count || 0}</strong>
                      </div>
                      <div className={styles.diagnosticRow}>
                        <span>Status</span>
                        <strong style={{ color: '#4ade80' }}>Success</strong>
                      </div>
                      <div className={styles.diagnosticRow}>
                        <span>Completed At</span>
                        <strong>{new Date().toLocaleString()}</strong>
                      </div>
                    </div>
                    {generationResult.products && generationResult.products.length > 0 && (
                      <div className={styles.zoneSectionCompact}>
                        <label className={styles.sectionLabel}>Sample Products (First 5)</label>
                        <div className={styles.diagnosticsCardExact}>
                          {generationResult.products.slice(0, 5).map((product, index) => (
                            <div key={product.id || index} className={styles.diagnosticRow}>
                              <span>Product {index + 1}</span>
                              <strong>
                                ${product.price} | {formatSize(product.size)} |
                                Logistics: {product.logistics?.toFixed(2)} |
                                Demand: {product.demand?.toFixed(2)}
                              </strong>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </section>
              )}

            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
