import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Compass,
  SlidersHorizontal,
  ChartSpline,
  Wrench,
  Folder,
  Upload,
  Plus,
  FileText,
  Save,
  Trash2,
  Copy,
  FilePenLine,
  Settings2,
} from "lucide-react";
import PriceChart from "../steps/PriceChart";
import RangeControl from "../controls/RangeControl";
import { BigControl } from "../controls/BigControl";
import layoutStyles from "../styles/ConsoleLayout.module.css";
import actionStyles from "../styles/ControlButton.module.css";
import statusStyles from "../styles/SystemPanel.module.css";
import {
  fetchGenerationConfig,
  updateGenerationConfig,
} from "../../api/configApi";




const toCumulativePercentBoundaries = (zoneList) => {
  const shares = normalizeZoneShares(zoneList).map((zone) => zone.span_share);

  return shares.slice(0, -1).reduce((accumulator, share) => {
    const previous = accumulator[accumulator.length - 1] ?? 0;
    const next = previous + share * 100;
    accumulator.push(Number(next.toFixed(4)));
    return accumulator;
  }, []);
};

const buildSeries = (min, max, yTemplate) => {
  const safeMin = Number.isFinite(min) ? min : 0;
  const safeMax = Number.isFinite(max) ? max : 100;
  const span = Math.max(1e-9, safeMax - safeMin);
  const source =
    Array.isArray(yTemplate) && yTemplate.length
      ? yTemplate
      : [0, 20, 40, 60, 80, 100];

  return source.map((value, index) => {
    const t = source.length > 1 ? index / (source.length - 1) : 0;
    return { x: safeMin + t * span, y: value };
  });
};

const normalizeZoneShares = (zoneList) => {
  const minSpan = APP_DEFAULTS.generation.guardrails.min_span;
  const safeList = (Array.isArray(zoneList) ? zoneList : []).map((zone) => ({
    ...zone,
    span_share: Math.max(minSpan, Number(zone?.span_share) || 0),
  }));

  if (!safeList.length) {
    return safeList;
  }

  const total = safeList.reduce((sum, zone) => sum + zone.span_share, 0);
  if (total <= 0) {
    const evenShare = 1 / safeList.length;
    return safeList.map((zone) => ({ ...zone, span_share: evenShare }));
  }

  return safeList.map((zone) => ({
    ...zone,
    span_share: zone.span_share / total,
  }));
};

const clampZoneForMode = (zone) => {
  const defaults = APP_DEFAULTS.generation.zoneDefaults;
  const guardrails = APP_DEFAULTS.generation.guardrails;
  const mode = String(zone?.mode ?? "exact");

  const next = {
    ...zone,
    mode,
    step: Math.max(guardrails.min_step, Number(zone?.step ?? defaults.step)),
    resolution: Math.max(
      guardrails.min_resolution,
      Number(zone?.resolution ?? defaults.resolution),
    ),
    bias: Math.max(guardrails.min_bias, Number(zone?.bias ?? defaults.bias)),
  };

  if (mode === "exact") {
    next.step = Math.max(
      guardrails.min_step,
      Number(next.step || defaults.step),
    );
  }

  if (mode === "geometric" || mode === "u_shape") {
    next.resolution = Math.max(
      guardrails.min_resolution,
      Number(next.resolution || defaults.resolution),
    );
  }

  if (mode === "power") {
    next.resolution = Math.max(
      guardrails.min_resolution,
      Number(next.resolution || defaults.resolution),
    );
    next.bias = Math.max(
      guardrails.min_bias,
      Number(next.bias || defaults.bias),
    );
  }

  return next;
};

export default function MainPage() {
  const [leftOpen, setLeftOpen] = useState(true);
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [yamlMode, setYamlMode] = useState(false);
  const [priceAdvancedOpen, setPriceAdvancedOpen] = useState(false);
  const [sizeAdvancedOpen, setSizeAdvancedOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState("json");

  const [budget, setBudget] = useState(APP_DEFAULTS.solver.budget);
  const [space, setSpace] = useState(APP_DEFAULTS.solver.space);
  const [priceMin, setPriceMin] = useState(
    APP_DEFAULTS.generation.priceRange[0],
  );
  const [priceMax, setPriceMax] = useState(
    APP_DEFAULTS.generation.priceRange[1],
  );
  const [sizeMin, setSizeMin] = useState(APP_DEFAULTS.generation.sizeRange[0]);
  const [sizeMax, setSizeMax] = useState(APP_DEFAULTS.generation.sizeRange[1]);

  const [activePriceZone, setActivePriceZone] = useState(0);
  const [activeSizeZone, setActiveSizeZone] = useState(0);

  const [yamlText, setYamlText] = useState(
    [
      "generation:",
      "  price_zones:",
      "    - span_share: 0.0019",
      "      mode: exact",
      "      step: 1.0",
      "  size_zones:",
      "    - span_share: 0.30",
      "      mode: u_shape",
      "      resolution: 352",
    ].join("\n"),
  );

  const [priceZones, setPriceZones] = useState(
    APP_DEFAULTS.generation.priceZones.map((zone) => ({ ...zone })),
  );

  const [sizeZones, setSizeZones] = useState(
    APP_DEFAULTS.generation.sizeZones.map((zone) => ({ ...zone })),
  );
  const [configLoaded, setConfigLoaded] = useState(false);
  const [saveState, setSaveState] = useState("idle");
  const isPersistingRef = useRef(false);

  const data = useMemo(
    () =>
      buildSeries(
        priceMin,
        priceMax,
        [8, 16, 25, 21, 35, 30, 42, 40, 53, 60, 68],
      ),
    [priceMin, priceMax],
  );

  const sizeData = useMemo(
    () =>
      buildSeries(
        sizeMin,
        sizeMax,
        [30, 24, 20, 28, 40, 55, 60, 50, 38, 32, 58],
      ),
    [sizeMin, sizeMax],
  );

  const priceGraphZones = useMemo(
    () => toCumulativePercentBoundaries(priceZones),
    [priceZones],
  );

  const sizeGraphZones = useMemo(
    () => toCumulativePercentBoundaries(sizeZones),
    [sizeZones],
  );

  const selectedPriceZone = priceZones[activePriceZone] ?? priceZones[0];
  const selectedSizeZone = sizeZones[activeSizeZone] ?? sizeZones[0];

  const navItems = [
    { icon: Compass, label: "Overview" },
    { icon: SlidersHorizontal, label: "Ranges" },
    { icon: ChartSpline, label: "Distributions" },
    { icon: Wrench, label: "Diagnostics" },
  ];

  const updatePriceZone = (index, patch) => {
    setPriceZones((previous) =>
      normalizeZoneShares(
        previous.map((zone, zoneIndex) =>
          zoneIndex === index ? clampZoneForMode({ ...zone, ...patch }) : zone,
        ),
      ),
    );
  };

  const updateSizeZone = (index, patch) => {
    setSizeZones((previous) =>
      normalizeZoneShares(
        previous.map((zone, zoneIndex) =>
          zoneIndex === index ? clampZoneForMode({ ...zone, ...patch }) : zone,
        ),
      ),
    );
  };

  const addPriceZoneTab = () => {
    setPriceZones((previous) => {
      const next = [
        ...previous,
        {
          ...APP_DEFAULTS.generation.zoneDefaults,
          mode: "exact",
          span_share: 0.1,
        },
      ];
      setActivePriceZone(next.length - 1);
      return normalizeZoneShares(next.map((zone) => clampZoneForMode(zone)));
    });
  };

  const addSizeZoneTab = () => {
    setSizeZones((previous) => {
      const next = [
        ...previous,
        {
          ...APP_DEFAULTS.generation.zoneDefaults,
          span_share: 0.1,
          mode: "u_shape",
          resolution: 128,
        },
      ];
      setActiveSizeZone(next.length - 1);
      return normalizeZoneShares(next.map((zone) => clampZoneForMode(zone)));
    });
  };

  const downloadText = (content, extension, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `price-graph.${extension}`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  };

  const exportGraph = () => {
    if (exportFormat === "yaml") {
      downloadText(yamlText, "yaml", "text/yaml");
      return;
    }

    if (exportFormat === "csv") {
      const rows = ["x,y", ...data.map((point) => `${point.x},${point.y}`)];
      downloadText(rows.join("\n"), "csv", "text/csv");
      return;
    }

    downloadText(
      JSON.stringify(
        {
          data,
          price_zone_boundaries_pct: priceGraphZones,
          size_zone_boundaries_pct: sizeGraphZones,
        },
        null,
        2,
      ),
      "json",
      "application/json",
    );
  };

  const saveSnapshot = () => {
    downloadText(
      JSON.stringify(
        {
          budget,
          space,
          price_range: [priceMin, priceMax],
          size_range: [sizeMin, sizeMax],
          price_zones: priceZones,
          size_zones: sizeZones,
        },
        null,
        2,
      ),
      "snapshot",
      "application/json",
    );
  };

  const addZone = () => {
    setPriceZones((previous) => {
      const next = [
        ...previous,
        { span_share: 0.01, mode: "exact", step: 1.0, resolution: 10 },
      ];
      setActivePriceZone(next.length - 1);
      return next;
    });
  };

  const loadPreset = () => {
    setPriceZones(
      APP_DEFAULTS.generation.priceZones.map((zone) => ({ ...zone })),
    );
    setActivePriceZone(0);
  };

  return (
    <div className={layoutStyles.root}>
      <header className={layoutStyles.header}>
        <button
          className={layoutStyles.headerButton}
          onClick={() => setLeftOpen((open) => !open)}
        ></button>

        <div className={layoutStyles.headerTitleWrap}>
          <div className={layoutStyles.headerTitle}>Simulation Console</div>
          <div className={layoutStyles.headerSubtitle}>
            Cartesian Product Enumeration · Generation View
          </div>
        </div>

        <div className={layoutStyles.headerGhost} />
      </header>

      <aside
        className={`${layoutStyles.sidebar} ${!leftOpen ? layoutStyles.sidebarCollapsed : ""}`}
      >
        <div className={layoutStyles.sidebarInner}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.label} className={layoutStyles.navIconButton}>
                <Icon size={14} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </aside>

      <main className={layoutStyles.main}>
        <section className={layoutStyles.initGrid}>
          <div className={layoutStyles.initPanel}>
            <BigControl
              label="Budget"
              value={budget}
              setValue={setBudget}
              max={1000000}
              accent="#434165"
              showGauge
              showModes={false}
            />
          </div>

          <div className={layoutStyles.initPanel}>
            <BigControl
              label="Space"
              value={space}
              setValue={setSpace}
              max={200000}
              accent="#305465"
              showGauge
              showModes={false}
            />
          </div>
        </section>

        <section className={layoutStyles.rangeGrid}>
          <RangeControl
            label="Price Range"
            minValue={priceMin}
            maxValue={priceMax}
            setMin={setPriceMin}
            setMax={setPriceMax}
            maxLimit={100000}
            accent="#4a3f73"
          />
          <RangeControl
            label="Size Range"
            minValue={sizeMin}
            maxValue={sizeMax}
            setMin={setSizeMin}
            setMax={setSizeMax}
            maxLimit={200000}
            accent="#2f5f6a"
          />
        </section>

        <section className={layoutStyles.graphGrid}>
          <section
            className={`${layoutStyles.graphCard} ${layoutStyles.graphCardPrice}`}
          >
            <div className={layoutStyles.graphHeader}>
              <h2>Price Range Distribution</h2>

              <div className={actionStyles.graphActions}>
                <button
                  className={actionStyles.actionButton}
                  onClick={addZone}
                  title="Add Zone"
                >
                  <Plus size={16} />
                </button>
                <button
                  className={actionStyles.actionButton}
                  onClick={loadPreset}
                  title="Load Preset"
                >
                  <Folder size={16} />
                </button>
                <button
                  className={actionStyles.actionButton}
                  onClick={() => setYamlMode((open) => !open)}
                  title="YAML Editor"
                >
                  <FileText size={16} />
                </button>
                <button
                  className={actionStyles.actionButton}
                  onClick={saveSnapshot}
                  title="Save Snapshot"
                >
                  <Save size={16} />
                </button>
                <button
                  className={actionStyles.actionButton}
                  onClick={exportGraph}
                  title="Export Graph"
                >
                  <Upload size={16} />
                </button>

                <select
                  className={layoutStyles.formatSelect}
                  value={exportFormat}
                  onChange={(event) => setExportFormat(event.target.value)}
                >
                  <option value="json">JSON</option>
                  <option value="yaml">YAML</option>
                  <option value="csv">CSV</option>
                </select>
              </div>
            </div>

            <PriceChart
              data={data}
              zones={priceGraphZones}
              zonesArePercent
              variant="price"
              xMin={priceMin}
              xMax={priceMax}
              zoomable
            />
          </section>

          <section
            className={`${layoutStyles.graphCard} ${layoutStyles.graphCardSize}`}
          >
            <div className={layoutStyles.graphHeader}>
              <h2>Size Range Distribution</h2>
            </div>
            <PriceChart
              data={sizeData}
              zones={sizeGraphZones}
              zonesArePercent
              variant="size"
              xMin={sizeMin}
              xMax={sizeMax}
              zoomable
            />
          </section>
        </section>

        <section className={layoutStyles.zoneSection}>
          <div className={layoutStyles.zoneGrid}>
            <div className={layoutStyles.zoneCard}>
              <div className={layoutStyles.zoneHeading}>Price Zones</div>

              <div className={layoutStyles.zoneTabBar}>
                <div
                  className={layoutStyles.zoneTabs}
                  role="tablist"
                  aria-label="Price zones"
                >
                  {priceZones.map((zone, index) => (
                    <div
                      key={`price-zone-${index}`}
                      role="tab"
                      tabIndex={0}
                      aria-selected={index === activePriceZone}
                      className={`${layoutStyles.zoneTab} ${index === activePriceZone ? layoutStyles.zoneTabActive : ""}`}
                      onClick={() => setActivePriceZone(index)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setActivePriceZone(index);
                        }
                      }}
                    >
                      Zone {index + 1}
                    </div>
                  ))}
                  <button
                    type="button"
                    className={`${layoutStyles.zoneTab} ${layoutStyles.zoneTabAdd}`}
                    onClick={addPriceZoneTab}
                    title="Add price zone"
                  >
                    +
                  </button>
                </div>

                <div className={layoutStyles.zoneToolbarActions}>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => {
                      if (priceZones.length <= 1) {
                        return;
                      }
                      setPriceZones((previous) =>
                        normalizeZoneShares(
                          previous
                            .filter((_, index) => index !== activePriceZone)
                            .map((zone) => clampZoneForMode(zone)),
                        ),
                      );
                      setActivePriceZone(0);
                    }}
                    title="Delete zone"
                  >
                    <Trash2 size={14} />
                  </button>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => {
                      const zoneToDuplicate = priceZones[activePriceZone];
                      if (zoneToDuplicate) {
                        setPriceZones((previous) => [
                          ...normalizeZoneShares(
                            [
                              ...previous,
                              clampZoneForMode({ ...zoneToDuplicate }),
                            ].map((zone) => clampZoneForMode(zone)),
                          ),
                        ]);
                      }
                    }}
                    title="Duplicate zone"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => setYamlMode(true)}
                    title="Switch to YAML editor"
                  >
                    <FilePenLine size={14} />
                  </button>
                  <button
                    className={`${layoutStyles.zoneIconButton} ${priceAdvancedOpen ? layoutStyles.zoneIconButtonActive : ""}`}
                    onClick={() => setPriceAdvancedOpen((open) => !open)}
                    title="Advanced settings"
                  >
                    <Settings2 size={14} />
                  </button>
                </div>
              </div>

              <div className={layoutStyles.zoneParamBlock}>
                <div className={layoutStyles.zoneControlRow}>
                  <div className={layoutStyles.zoneControlLabel}>
                    Span Share
                  </div>
                  <input
                    className={layoutStyles.inputSlider}
                    type="range"
                    min="0"
                    max="1"
                    step="0.0001"
                    value={selectedPriceZone.span_share}
                    onChange={(event) =>
                      updatePriceZone(activePriceZone, {
                        span_share: Number(event.target.value),
                      })
                    }
                  />
                  <div className={layoutStyles.zoneControlValue}>
                    {selectedPriceZone.span_share.toFixed(4)}
                  </div>
                </div>

                <div className={layoutStyles.zoneControlRow}>
                  <div className={layoutStyles.zoneControlLabel}>Mode</div>
                  <div className={layoutStyles.zoneSpacer} />
                  <select
                    className={layoutStyles.modeSelect}
                    value={selectedPriceZone.mode}
                    onChange={(event) =>
                      updatePriceZone(activePriceZone, {
                        mode: event.target.value,
                      })
                    }
                  >
                    <option value="exact">exact</option>
                    <option value="geometric">geometric</option>
                  </select>
                </div>

                {selectedPriceZone.mode === "exact" ? (
                  <div className={layoutStyles.zoneControlRow}>
                    <div className={layoutStyles.zoneControlLabel}>Step</div>
                    <input
                      className={layoutStyles.inputSlider}
                      type="range"
                      min={APP_DEFAULTS.generation.guardrails.min_step}
                      max="100"
                      step="1"
                      value={selectedPriceZone.step}
                      onChange={(event) =>
                        updatePriceZone(activePriceZone, {
                          step: Number(event.target.value),
                        })
                      }
                    />
                    <div className={layoutStyles.zoneControlValue}>
                      {selectedPriceZone.step.toFixed(1)}
                    </div>
                  </div>
                ) : (
                  <div className={layoutStyles.zoneControlRow}>
                    <div className={layoutStyles.zoneControlLabel}>
                      Resolution
                    </div>
                    <input
                      className={layoutStyles.inputSlider}
                      type="range"
                      min={APP_DEFAULTS.generation.guardrails.min_resolution}
                      max="512"
                      step="1"
                      value={selectedPriceZone.resolution}
                      onChange={(event) =>
                        updatePriceZone(activePriceZone, {
                          resolution: Number(event.target.value),
                        })
                      }
                    />
                    <div className={layoutStyles.zoneControlValue}>
                      {selectedPriceZone.resolution.toFixed(0)}
                    </div>
                  </div>
                )}

                {priceAdvancedOpen && (
                  <div className={layoutStyles.advancedPanel}>
                    <div className={layoutStyles.zoneControlRow}>
                      <div className={layoutStyles.zoneControlLabel}>
                        Sampler
                      </div>
                      <div className={layoutStyles.zoneSpacer} />
                      <select
                        className={layoutStyles.modeSelect}
                        value={selectedPriceZone.sampler ?? "balanced"}
                        onChange={(event) =>
                          updatePriceZone(activePriceZone, {
                            sampler: event.target.value,
                          })
                        }
                      >
                        <option value="strict">strict</option>
                        <option value="balanced">balanced</option>
                        <option value="fast">fast</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className={layoutStyles.zoneCard}>
              <div className={layoutStyles.zoneHeading}>Size Zones</div>

              <div className={layoutStyles.zoneTabBar}>
                <div
                  className={layoutStyles.zoneTabs}
                  role="tablist"
                  aria-label="Size zones"
                >
                  {sizeZones.map((zone, index) => (
                    <div
                      key={`size-zone-${index}`}
                      role="tab"
                      tabIndex={0}
                      aria-selected={index === activeSizeZone}
                      className={`${layoutStyles.zoneTab} ${index === activeSizeZone ? layoutStyles.zoneTabActive : ""}`}
                      onClick={() => setActiveSizeZone(index)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setActiveSizeZone(index);
                        }
                      }}
                    >
                      Zone {index + 1}
                    </div>
                  ))}
                  <button
                    type="button"
                    className={`${layoutStyles.zoneTab} ${layoutStyles.zoneTabAdd}`}
                    onClick={addSizeZoneTab}
                    title="Add size zone"
                  >
                    +
                  </button>
                </div>

                <div className={layoutStyles.zoneToolbarActions}>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => {
                      if (sizeZones.length <= 1) {
                        return;
                      }
                      setSizeZones((previous) =>
                        normalizeZoneShares(
                          previous
                            .filter((_, index) => index !== activeSizeZone)
                            .map((zone) => clampZoneForMode(zone)),
                        ),
                      );
                      setActiveSizeZone(0);
                    }}
                    title="Delete zone"
                  >
                    <Trash2 size={14} />
                  </button>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => {
                      const zoneToDuplicate = sizeZones[activeSizeZone];
                      if (zoneToDuplicate) {
                        setSizeZones((previous) => [
                          ...normalizeZoneShares(
                            [
                              ...previous,
                              clampZoneForMode({ ...zoneToDuplicate }),
                            ].map((zone) => clampZoneForMode(zone)),
                          ),
                        ]);
                      }
                    }}
                    title="Duplicate zone"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    className={layoutStyles.zoneIconButton}
                    onClick={() => setYamlMode(true)}
                    title="Switch to YAML editor"
                  >
                    <FilePenLine size={14} />
                  </button>
                  <button
                    className={`${layoutStyles.zoneIconButton} ${sizeAdvancedOpen ? layoutStyles.zoneIconButtonActive : ""}`}
                    onClick={() => setSizeAdvancedOpen((open) => !open)}
                    title="Advanced settings"
                  >
                    <Settings2 size={14} />
                  </button>
                </div>
              </div>

              <div className={layoutStyles.zoneParamBlock}>
                <div className={layoutStyles.zoneControlRow}>
                  <div className={layoutStyles.zoneControlLabel}>
                    Span Share
                  </div>
                  <input
                    className={layoutStyles.inputSlider}
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={selectedSizeZone.span_share}
                    onChange={(event) =>
                      updateSizeZone(activeSizeZone, {
                        span_share: Number(event.target.value),
                      })
                    }
                  />
                  <div className={layoutStyles.zoneControlValue}>
                    {selectedSizeZone.span_share.toFixed(2)}
                  </div>
                </div>

                <div className={layoutStyles.zoneControlRow}>
                  <div className={layoutStyles.zoneControlLabel}>Mode</div>
                  <div className={layoutStyles.zoneSpacer} />
                  <select
                    className={layoutStyles.modeSelect}
                    value={selectedSizeZone.mode}
                    onChange={(event) =>
                      updateSizeZone(activeSizeZone, {
                        mode: event.target.value,
                      })
                    }
                  >
                    <option value="u_shape">u_shape</option>
                    <option value="power">power</option>
                    <option value="exact">exact</option>
                  </select>
                </div>

                {selectedSizeZone.mode === "exact" ? (
                  <div className={layoutStyles.zoneControlRow}>
                    <div className={layoutStyles.zoneControlLabel}>Step</div>
                    <input
                      className={layoutStyles.inputSlider}
                      type="range"
                      min={APP_DEFAULTS.generation.guardrails.min_step}
                      max="100"
                      step="1"
                      value={selectedSizeZone.step}
                      onChange={(event) =>
                        updateSizeZone(activeSizeZone, {
                          step: Number(event.target.value),
                        })
                      }
                    />
                    <div className={layoutStyles.zoneControlValue}>
                      {selectedSizeZone.step.toFixed(1)}
                    </div>
                  </div>
                ) : (
                  <div className={layoutStyles.zoneControlRow}>
                    <div className={layoutStyles.zoneControlLabel}>
                      Resolution
                    </div>
                    <input
                      className={layoutStyles.inputSlider}
                      type="range"
                      min={APP_DEFAULTS.generation.guardrails.min_resolution}
                      max="512"
                      step="1"
                      value={selectedSizeZone.resolution}
                      onChange={(event) =>
                        updateSizeZone(activeSizeZone, {
                          resolution: Number(event.target.value),
                        })
                      }
                    />
                    <div className={layoutStyles.zoneControlValue}>
                      {selectedSizeZone.resolution.toFixed(0)}
                    </div>
                  </div>
                )}

                {selectedSizeZone.mode === "power" && (
                  <div className={layoutStyles.zoneControlRow}>
                    <div className={layoutStyles.zoneControlLabel}>Bias</div>
                    <input
                      className={layoutStyles.inputSlider}
                      type="range"
                      min={APP_DEFAULTS.generation.guardrails.min_bias}
                      max="4"
                      step="0.01"
                      value={selectedSizeZone.bias}
                      onChange={(event) =>
                        updateSizeZone(activeSizeZone, {
                          bias: Number(event.target.value),
                        })
                      }
                    />
                    <div className={layoutStyles.zoneControlValue}>
                      {selectedSizeZone.bias.toFixed(2)}
                    </div>
                  </div>
                )}

                {sizeAdvancedOpen && (
                  <div className={layoutStyles.advancedPanel}>
                    <div className={layoutStyles.zoneControlRow}>
                      <div className={layoutStyles.zoneControlLabel}>Curve</div>
                      <div className={layoutStyles.zoneSpacer} />
                      <select
                        className={layoutStyles.modeSelect}
                        value={selectedSizeZone.curve ?? "balanced"}
                        onChange={(event) =>
                          updateSizeZone(activeSizeZone, {
                            curve: event.target.value,
                          })
                        }
                      >
                        <option value="balanced">balanced</option>
                        <option value="edge_heavy">edge_heavy</option>
                        <option value="center_heavy">center_heavy</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {yamlMode && (
          <section className={layoutStyles.yamlCard}>
            <div className={layoutStyles.yamlHeader}>
              YAML Editor · generation
            </div>
            <textarea
              value={yamlText}
              onChange={(event) => setYamlText(event.target.value)}
              className={layoutStyles.yamlInput}
            />
          </section>
        )}
      </main>

      <footer className={layoutStyles.bottomPanel}>
        <div className={statusStyles.leftCluster}>
          <span className={statusStyles.statusItem}>
            <span
              className={`${statusStyles.statusDot} ${statusStyles.running}`}
            />
            Docker: Running
          </span>
          <span className={statusStyles.statusItem}>
            <span
              className={`${statusStyles.statusDot} ${statusStyles.running}`}
            />
            DB: Connected
          </span>
          <span className={statusStyles.statusItem}>
            <span
              className={`${statusStyles.statusDot} ${statusStyles.idle}`}
            />
            Engine: Idle
          </span>
          <span className={statusStyles.statusItem}>Solver: 12ms</span>
          <span className={statusStyles.statusItem}>Hash: cfg-7fa9</span>
          <span className={statusStyles.statusItem}>Memory: 412MB</span>
        </div>

        <div className={layoutStyles.statusScroller}>
          autosave:on · export:ready · snapshot:queued · logs:0 · solver_idle ·
          distribution_synced · yaml_linked
        </div>

        <div className={statusStyles.rightCluster}>
          <button
            className={layoutStyles.terminalCaret}
            onClick={() => setTerminalOpen((open) => !open)}
            title="Toggle terminal"
          >
            ^
          </button>
        </div>
      </footer>

      {terminalOpen && (
        <section className={layoutStyles.terminalPopup}>
          <div className={layoutStyles.terminalTitle}>Terminal</div>
          <div className={layoutStyles.terminalBody}>
            $ engine status\nidle\n$ db ping\nok\n$ docker ps\nsolver-container
            · running
          </div>
        </section>
      )}
    </div>
  );
}
