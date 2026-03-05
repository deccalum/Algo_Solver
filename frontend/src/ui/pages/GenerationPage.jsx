import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
    Plus,
    FileText,
    Save,
    Trash2,
    Copy,
    FilePenLine,
    Settings2,
    Folder,
    Upload,
} from "lucide-react";
import PriceChart from "../steps/PriceChart";
import RangeControl from "../controls/RangeControl";
import { BigControl } from "../controls/BigControl";
import layoutStyles from "../styles/ConsoleLayout.module.css";
import actionStyles from "../styles/ControlButton.module.css";
import {
    fetchGenerationConfig,
    updateGenerationConfig,
} from "../../api/configApi";
import { APP_DEFAULTS } from "../../constants/appDefaults";

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

export default function GenerationPage() {
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

    const [priceZones, setPriceZones] = useState(
        APP_DEFAULTS.generation.priceZones.map((zone) => ({ ...zone })),
    );

    const [sizeZones, setSizeZones] = useState(
        APP_DEFAULTS.generation.sizeZones.map((zone) => ({ ...zone })),
    );

    const selectedPriceZone = priceZones[activePriceZone] || {};
    const selectedSizeZone = sizeZones[activeSizeZone] || {};

    const priceGraphZones = useMemo(
        () =>
            toCumulativePercentBoundaries(
                priceZones.map((zone) => clampZoneForMode(zone)),
            ),
        [priceZones],
    );

    const sizeGraphZones = useMemo(
        () =>
            toCumulativePercentBoundaries(
                sizeZones.map((zone) => clampZoneForMode(zone)),
            ),
        [sizeZones],
    );

    const data = useMemo(
        () =>
            buildSeries(priceMin, priceMax, selectedPriceZone.y_template).map(
                (p) => ({
                    ...p,
                    fill: "#6366f1",
                }),
            ),
        [priceMin, priceMax, selectedPriceZone],
    );

    const sizeData = useMemo(
        () =>
            buildSeries(sizeMin, sizeMax, selectedSizeZone.y_template).map((p) => ({
                ...p,
                fill: "#06b6d4",
            })),
        [sizeMin, sizeMax, selectedSizeZone],
    );

    const updatePriceZone = useCallback((index, updates) => {
        setPriceZones((previous) => {
            const next = [...previous];
            next[index] = { ...next[index], ...updates };
            return normalizeZoneShares(next.map((zone) => clampZoneForMode(zone)));
        });
    }, []);

    const updateSizeZone = useCallback((index, updates) => {
        setSizeZones((previous) => {
            const next = [...previous];
            next[index] = { ...next[index], ...updates };
            return normalizeZoneShares(next.map((zone) => clampZoneForMode(zone)));
        });
    }, []);

    const downloadText = (text, filename, mimeType) => {
        const blob = new Blob([text], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const exportGraph = () => {
        const exportData = {
            budget,
            space,
            price_range: [priceMin, priceMax],
            size_range: [sizeMin, sizeMax],
            price_zones: priceZones,
            size_zones: sizeZones,
        };

        if (exportFormat === "json") {
            downloadText(
                JSON.stringify(exportData, null, 2),
                "export",
                "application/json",
            );
        } else if (exportFormat === "yaml") {
            downloadText(
                JSON.stringify(exportData, null, 2),
                "export.yaml",
                "text/yaml",
            );
        }
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

    const loadPreset = () => {
        setPriceZones(
            APP_DEFAULTS.generation.priceZones.map((zone) => ({ ...zone })),
        );
        setActivePriceZone(0);
    };

    return (
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
                                onClick={addPriceZoneTab}
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
                            <div className={layoutStyles.zoneTabs} role="tablist">
                                {priceZones.map((zone, index) => (
                                    <div
                                        key={`price-zone-${index}`}
                                        role="tab"
                                        tabIndex={0}
                                        aria-selected={index === activePriceZone}
                                        className={`${layoutStyles.zoneTab} ${index === activePriceZone ? layoutStyles.zoneTabActive : ""
                                            }`}
                                        onClick={() => setActivePriceZone(index)}
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
                        </div>

                        <div className={layoutStyles.zoneParamBlock}>
                            <div className={layoutStyles.zoneControlRow}>
                                <div className={layoutStyles.zoneControlLabel}>Span Share</div>
                                <input
                                    className={layoutStyles.inputSlider}
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.0001"
                                    value={selectedPriceZone.span_share || 0}
                                    onChange={(event) =>
                                        updatePriceZone(activePriceZone, {
                                            span_share: Number(event.target.value),
                                        })
                                    }
                                />
                                <div className={layoutStyles.zoneControlValue}>
                                    {(selectedPriceZone.span_share || 0).toFixed(4)}
                                </div>
                            </div>

                            <div className={layoutStyles.zoneControlRow}>
                                <div className={layoutStyles.zoneControlLabel}>Mode</div>
                                <select
                                    className={layoutStyles.modeSelect}
                                    value={selectedPriceZone.mode || "exact"}
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
                        </div>
                    </div>

                    <div className={layoutStyles.zoneCard}>
                        <div className={layoutStyles.zoneHeading}>Size Zones</div>

                        <div className={layoutStyles.zoneTabBar}>
                            <div className={layoutStyles.zoneTabs} role="tablist">
                                {sizeZones.map((zone, index) => (
                                    <div
                                        key={`size-zone-${index}`}
                                        role="tab"
                                        tabIndex={0}
                                        aria-selected={index === activeSizeZone}
                                        className={`${layoutStyles.zoneTab} ${index === activeSizeZone ? layoutStyles.zoneTabActive : ""
                                            }`}
                                        onClick={() => setActiveSizeZone(index)}
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
                        </div>

                        <div className={layoutStyles.zoneParamBlock}>
                            <div className={layoutStyles.zoneControlRow}>
                                <div className={layoutStyles.zoneControlLabel}>Span Share</div>
                                <input
                                    className={layoutStyles.inputSlider}
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.01"
                                    value={selectedSizeZone.span_share || 0}
                                    onChange={(event) =>
                                        updateSizeZone(activeSizeZone, {
                                            span_share: Number(event.target.value),
                                        })
                                    }
                                />
                                <div className={layoutStyles.zoneControlValue}>
                                    {(selectedSizeZone.span_share || 0).toFixed(2)}
                                </div>
                            </div>

                            <div className={layoutStyles.zoneControlRow}>
                                <div className={layoutStyles.zoneControlLabel}>Mode</div>
                                <select
                                    className={layoutStyles.modeSelect}
                                    value={selectedSizeZone.mode || "u_shape"}
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
                        </div>
                    </div>
                </div>
            </section>
        </main>
    );
}
