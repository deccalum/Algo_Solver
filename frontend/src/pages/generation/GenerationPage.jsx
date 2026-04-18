import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate, useOutletContext } from 'react-router-dom';
import { getTemplates, getTemplate, postCount, postGenerate, getSolarPsh } from '../../api/client';
import { CombinationStrip } from './CombinationStrip';
import { GenSidebar } from './GenSidebar';
import { ParamCard } from './ParamCard';
import { InfluenceSection } from './InfluenceSection';
import { ConstraintSection } from './ConstraintSection';
import { LogifierCard, DEFAULT_LOGIFIER } from './LogifierCard';
import { SpecifyProductModal } from './SpecifyProductModal';
import '../../styles/generation-page.css';

// ── Solar location tool ───────────────────────────────────────────────────────
// Only rendered when the solar_panel template is active.
// Fetches peak sun hours from /api/solar/psh and applies seasonal min/max to
// the sunlight_hours param range.
function SolarLocationTool({ params, onParamsChange }) {
  const [lat,    setLat]    = useState('');
  const [tilt,   setTilt]   = useState('');
  const [result, setResult] = useState(null);
  const [busy,   setBusy]   = useState(false);
  const [error,  setError]  = useState(null);

  async function handleApply() {
    const latNum = parseFloat(lat);
    if (isNaN(latNum) || latNum < -90 || latNum > 90) {
      setError('Enter a valid latitude (−90 to +90).');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const tiltNum = tilt !== '' ? parseFloat(tilt) : undefined;
      const data    = await getSolarPsh(latNum, tiltNum, undefined);
      setResult(data);
      // Apply seasonal range to sunlight_hours param
      onParamsChange(prev => prev.map(p =>
        p.name === 'sunlight_hours'
          ? { ...p, min: data.seasonal_min_psh, max: data.seasonal_max_psh }
          : p
      ));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="solar-tool">
      <div className="solar-tool__header">
        <span className="solar-tool__title">LOCATION CALCULATOR</span>
        <span className="solar-tool__subtitle">Derive sunlight hours from coordinates</span>
      </div>
      <div className="solar-tool__row">
        <label className="solar-tool__label">
          Latitude
          <input
            className="solar-tool__input"
            type="number"
            min="-90" max="90" step="0.01"
            placeholder="e.g. 51.5 (London)"
            value={lat}
            onChange={e => setLat(e.target.value)}
          />
        </label>
        <label className="solar-tool__label">
          Tilt °
          <input
            className="solar-tool__input"
            type="number"
            min="0" max="90" step="1"
            placeholder={lat ? `auto (${Math.abs(parseFloat(lat) || 0).toFixed(0)}°)` : 'auto = |lat|'}
            value={tilt}
            onChange={e => setTilt(e.target.value)}
          />
        </label>
        <button
          className="solar-tool__btn"
          onClick={handleApply}
          disabled={busy}
        >
          {busy ? '…' : 'APPLY'}
        </button>
      </div>
      {error && <p className="solar-tool__error">{error}</p>}
      {result && (
        <div className="solar-tool__result">
          <span className="solar-tool__stat">
            Today <strong>{result.psh} h</strong>
          </span>
          <span className="solar-tool__stat">
            Annual avg <strong>{result.annual_avg_psh} h</strong>
          </span>
          <span className="solar-tool__stat">
            Seasonal <strong>{result.seasonal_min_psh}–{result.seasonal_max_psh} h</strong>
          </span>
          <span className="solar-tool__stat solar-tool__stat--applied">
            ✓ Applied to sunlight_hours range
          </span>
        </div>
      )}
    </div>
  );
}

const DEFAULT_PARAM = {
  name: 'param',
  dist: 'uniform',
  min: 0,
  max: 100,
  dist_kwargs: { resolution: 10 },
};

// Apply a loaded template's data to local state.
function applyTemplate(t, setParams, setInfluences, setConstraints, setObjective, setSessionCtx) {
  setParams(t.params);
  setInfluences(t.influences);
  if (t.constraints?.length) setConstraints(t.constraints);
  if (t.objective_param)     setObjective({ param: t.objective_param, sense: t.objective_sense });
  setSessionCtx(prev => ({ ...prev, templateName: t.name }));
}

export function GenerationPage() {
  const location   = useLocation();
  const navigate   = useNavigate();
  const { setSessionCtx } = useOutletContext();

  // templateName comes from router state (set by StartPage) or falls back to the
  // first available template once the list is loaded.
  const routeTemplate = location.state?.template || null;

  const [templates,         setTemplates]         = useState([]);
  const [templateName,      setTemplateName]       = useState(routeTemplate);
  const [params,            setParams]             = useState([]);
  const [influences,        setInfluences]         = useState([]);
  const [constraints,       setConstraints]        = useState([]);
  const [objective,         setObjective]          = useState({ param: 'demand', sense: 'maximize' });
  const [count,             setCount]              = useState(null);
  const [isOverLimit,       setIsOverLimit]        = useState(false);
  const [saving,            setSaving]             = useState(false);
  const [activeSection,     setActiveSection]      = useState('parameters');
  const [loading,           setLoading]            = useState(true);
  const [logifierConfig,    setLogifierConfig]     = useState(DEFAULT_LOGIFIER);
  const [specifiedProducts, setSpecifiedProducts]  = useState([]);
  const [showProductModal,  setShowProductModal]   = useState(false);

  const countTimer = useRef(null);

  // ── 1. Load the template list ──────────────────────────────────────────────
  useEffect(() => {
    getTemplates()
      .then(list => {
        setTemplates(list);
        // If no template was specified in the route, default to the first one.
        if (!routeTemplate && list.length > 0) {
          setTemplateName(list[0].name);
        }
      })
      .catch(() => {});
  }, [routeTemplate]);

  // ── 2. Load the active template whenever templateName changes ──────────────
  useEffect(() => {
    if (!templateName) return;
    setLoading(true);
    getTemplate(templateName)
      .then(t => {
        applyTemplate(t, setParams, setInfluences, setConstraints, setObjective, setSessionCtx);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [templateName, setSessionCtx]);

  // ── 3. Debounced combination count ─────────────────────────────────────────
  const refreshCount = useCallback(() => {
    if (countTimer.current) clearTimeout(countTimer.current);
    countTimer.current = setTimeout(async () => {
      if (params.length === 0) return;
      try {
        const res = await postCount({ params, influences, logifier: logifierConfig });
        setCount(res.count);
        setIsOverLimit(!res.ok);
        setSessionCtx(prev => ({ ...prev, combinationCount: res.count }));
      } catch {
        // silent
      }
    }, 300);
  }, [params, influences, logifierConfig, setSessionCtx]);

  useEffect(() => {
    refreshCount();
    return () => { if (countTimer.current) clearTimeout(countTimer.current); };
  }, [params, logifierConfig, refreshCount]);

  // ── Param helpers ──────────────────────────────────────────────────────────
  const perAxis = params.map(p => p.dist_kwargs?.resolution ?? 10).join(' × ');

  function updateParam(idx, updated) {
    setParams(prev => prev.map((p, i) => i === idx ? updated : p));
  }

  function removeParam(idx) {
    setParams(prev => prev.filter((_, i) => i !== idx));
  }

  function addParam() {
    const name = `param_${params.length + 1}`;
    setParams(prev => [...prev, { ...DEFAULT_PARAM, name }]);
  }

  // ── Template switcher ──────────────────────────────────────────────────────
  function handleTemplateChange(name) {
    if (name === templateName) return;
    setTemplateName(name);
  }

  // ── Reset to template defaults ─────────────────────────────────────────────
  function handleReset() {
    if (!templateName) return;
    setLoading(true);
    getTemplate(templateName)
      .then(t => {
        applyTemplate(t, setParams, setInfluences, setConstraints, setObjective, setSessionCtx);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }

  // ── Generate & navigate to solver ──────────────────────────────────────────
  async function handleSave() {
    setSaving(true);
    try {
      const res = await postGenerate({ params, influences, logifier: logifierConfig });
      navigate('/solver', {
        state: {
          runId:           res.run_id,
          constraints,
          objectiveParam:  objective.param,
          objectiveSense:  objective.sense,
          specifiedProducts,
        },
      });
    } catch (err) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  // ── Section scroll ─────────────────────────────────────────────────────────
  function scrollToSection(id) {
    setActiveSection(id);
    document.getElementById(`section-${id}`)?.scrollIntoView({ behavior: 'smooth' });
  }

  if (loading) {
    return (
      <div className="generation-page__loading-wrapper">
        <div className="generation-page__loading-text">Loading template...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="generation-page__strip-wrapper">
        <CombinationStrip
          count={count}
          perAxis={perAxis}
          isOverLimit={isOverLimit}
          filtered={logifierConfig.enabled}
          onReset={handleReset}
          onSave={handleSave}
          saving={saving}
        />
      </div>

      <div className="generation-page__container">
        <GenSidebar
          activeSection={activeSection}
          templateName={templateName}
          templates={templates}
          paramCount={params.length}
          influenceCount={influences.length}
          onSectionClick={scrollToSection}
          onTemplateChange={handleTemplateChange}
        />

        <div className="generation-page__content custom-scrollbar">
          {/* Parameters */}
          <div id="section-parameters">
            <div className="generation-page__section-header">
              <span className="generation-page__section-title">PARAMETER AXES</span>
              <div className="generation-page__section-actions">
                <button
                  className="generation-page__specify-btn"
                  onClick={() => setShowProductModal(true)}
                >
                  + SPECIFY PRODUCT
                  {specifiedProducts.length > 0 && (
                    <span className="generation-page__specify-badge">
                      {specifiedProducts.length}
                    </span>
                  )}
                </button>
                <button
                  className="generation-page__add-param-btn"
                  onClick={addParam}
                >
                  + ADD PARAM
                </button>
              </div>
            </div>
            {templateName === 'solar_panel' && (
              <SolarLocationTool params={params} onParamsChange={setParams} />
            )}
            <div className="generation-page__param-list">
              {params.map((p, i) => (
                <ParamCard
                  key={`${p.name}-${i}`}
                  param={p}
                  index={i}
                  onChange={(updated) => updateParam(i, updated)}
                  onRemove={() => removeParam(i)}
                />
              ))}
            </div>
          </div>

          {/* Filter */}
          <div id="section-filter">
            <LogifierCard config={logifierConfig} onChange={setLogifierConfig} />
          </div>

          {/* Influences */}
          <div id="section-influences">
            <InfluenceSection
              influences={influences}
              params={params}
              onChange={setInfluences}
            />
          </div>

          {/* Constraints */}
          <div id="section-constraints">
            <ConstraintSection
              constraints={constraints}
              params={params}
              onChange={setConstraints}
            />
          </div>

          {/* Bottom actions */}
          <div className="generation-page__bottom-actions">
            <button
              className="generation-page__reset-btn"
              onClick={handleReset}
              disabled={!templateName}
            >
              Reset defaults
            </button>
            <button
              className="generation-page__save-btn"
              onClick={handleSave}
              disabled={saving || isOverLimit || params.length === 0}
            >
              {saving ? 'GENERATING...' : 'SAVE & SOLVE'}
            </button>
          </div>
        </div>
      </div>

      {showProductModal && (
        <SpecifyProductModal
          products={specifiedProducts}
          onChange={setSpecifiedProducts}
          onClose={() => setShowProductModal(false)}
        />
      )}
    </div>
  );
}
