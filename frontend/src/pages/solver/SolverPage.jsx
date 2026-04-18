import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getRun, getSolve, postSolve } from '../../api/client';
import { Icon } from '../../components/shared/Icon';
import { SourceRunCard } from './SourceRunCard';
import { ObjectiveSelector } from './ObjectiveSelector';
import { ConstraintList } from './ConstraintList';
import { MetricsPanel } from './MetricsPanel';
import { SelectionsTable } from './SelectionsTable';
import { SolverConsole } from './SolverConsole';
import '../../styles/solver-page.css';

function CommittedProductsCard({ products, constraints }) {
  const totalCost   = products.reduce((s, p) => s + p.price * p.amount, 0);
  const totalVolume = products.reduce((s, p) => s + p.volume * p.amount, 0);
  const totalWeight = products.reduce((s, p) => s + (p.weight ?? 0) * p.amount, 0);

  const budgetConstraint = constraints.find(c => c.param_name === 'price');
  const spaceConstraint  = constraints.find(c => c.param_name === 'volume');

  return (
    <div className="committed-products">
      <div className="committed-products__header">
        <span className="committed-products__title">
          COMMITTED PRODUCTS
        </span>
        <span className="committed-products__count">
          {products.length} item{products.length !== 1 ? 's' : ''}
        </span>
      </div>
      <div className="committed-products__body">
        {products.map((p, i) => (
          <div key={i} className="committed-products__item">
            <div className="committed-products__item-info">
              <span className="committed-products__item-name">{p.name}</span>
              <div className="committed-products__item-meta">
                <span>${p.price.toLocaleString()} × {p.amount} unit{p.amount !== 1 ? 's' : ''}</span>
                <span>{p.volume.toFixed(3)} m³/unit</span>
                {p.weight != null && <span>{p.weight} kg/unit</span>}
              </div>
            </div>
            <div className="committed-products__item-values">
              <div className="committed-products__item-cost">${(p.price * p.amount).toLocaleString()}</div>
              <div className="committed-products__item-vol">{(p.volume * p.amount).toFixed(3)} m³</div>
            </div>
          </div>
        ))}

        <div className="committed-products__totals">
          <div>
            <span className="committed-products__total-label">Total cost</span>
            <span className="committed-products__total-value committed-products__total-value--cost">
              ${totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
            {budgetConstraint && (
              <span className="committed-products__total-remaining">
                of ${budgetConstraint.bound.toLocaleString()} → ${(budgetConstraint.bound - totalCost).toLocaleString()} remaining
              </span>
            )}
          </div>
          <div>
            <span className="committed-products__total-label">Total space</span>
            <span className="committed-products__total-value committed-products__total-value--space">{totalVolume.toFixed(3)} m³</span>
            {spaceConstraint && (
              <span className="committed-products__total-remaining">
                of {spaceConstraint.bound} m³ → {(spaceConstraint.bound - totalVolume).toFixed(3)} remaining
              </span>
            )}
          </div>
          {totalWeight > 0 && (
            <div>
              <span className="committed-products__total-label">Total weight</span>
              <span className="committed-products__total-value committed-products__total-value--weight">{totalWeight.toFixed(1)} kg</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function timestamp() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
}

export function SolverPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const runId = location.state?.runId;
  const initialConstraints = location.state?.constraints || [];
  const initialObjectiveParam = location.state?.objectiveParam || 'demand';
  const initialObjectiveSense = location.state?.objectiveSense || 'maximize';
  const specifiedProducts = location.state?.specifiedProducts || [];

  const [sourceRun, setSourceRun] = useState(null);
  const [objectiveParam, setObjectiveParam] = useState(initialObjectiveParam);
  const [objectiveSense, setObjectiveSense] = useState(initialObjectiveSense);
  const [constraints, setConstraints] = useState(initialConstraints);
  const [solveResult, setSolveResult] = useState(null);
  const [solving, setSolving] = useState(false);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(!!runId);

  const paramNames = sourceRun?.params?.map(p => p.name) || [];

  useEffect(() => {
    if (!runId) return;
    getRun(runId).then(run => {
      setSourceRun(run);
      if (run.params.length > 0 && !run.params.some(p => p.name === objectiveParam)) {
        setObjectiveParam(run.params[0].name);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [runId]);

  function addLog(level, message) {
    setLogs(prev => [...prev, { time: timestamp(), level, message }]);
  }

  async function handleSolve() {
    if (!runId) return;
    setSolving(true);
    setSolveResult(null);

    addLog('INFO', `Loading model from run ${runId.slice(0, 8)}...`);
    addLog('SCIP', `Presolve: ${sourceRun?.item_count || '?'} variables, ${constraints.length} constraints`);

    const startTime = Date.now();
    addLog('EXEC', 'Running branch-and-bound optimization...');

    try {
      const res = await postSolve({
        generation_run_id: runId,
        constraints,
        objective_param: objectiveParam,
        objective_sense: objectiveSense,
        specified_products: specifiedProducts.length > 0 ? specifiedProducts : undefined,
      });

      const solveTime = Date.now() - startTime;
      addLog('OK', `Solve complete. Optimal found. (${solveTime}ms)`);

      // Fetch full solve details with selections
      const detail = await getSolve(res.solve_id);
      setSolveResult({ ...detail, solveTime });
    } catch (err) {
      addLog('ERR', `Solve failed: ${err.message}`);
    } finally {
      setSolving(false);
    }
  }

  if (loading) {
    return (
      <div className="solver-page__wrapper">
        <div className="solver-page__center-msg solver-page__center-msg--loading">Loading run data...</div>
      </div>
    );
  }

  if (!runId) {
    return (
      <div className="solver-page__wrapper">
        <div className="solver-page__center-msg">
          <p>No generation run selected.</p>
          <button
            className="solver-page__go-btn"
            onClick={() => navigate('/generation')}
          >
            Go to Generation
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Action Strip */}
      <div className="solver-page__action-strip">
        <div className="solver-page__strip-left">
          <div className="solver-page__strip-left" style={{ gap: '0.5rem' }}>
            <span className="solver-page__strip-label">Obj:</span>
            <span className="solver-page__strip-value">
              {objectiveSense.toUpperCase()} {objectiveParam}
            </span>
          </div>
          <div className="solver-page__strip-divider" />
          <div className="solver-page__strip-left" style={{ gap: '0.5rem' }}>
            <span className="solver-page__strip-label solver-page__strip-hidden-sm">Constraints:</span>
            <span className="solver-page__strip-pill">
              {constraints.length} active
            </span>
          </div>
          {specifiedProducts.length > 0 && (
            <>
              <div className="solver-page__strip-divider" />
              <div className="solver-page__strip-left" style={{ gap: '0.5rem' }}>
                <span className="solver-page__strip-label solver-page__strip-hidden-sm">Committed:</span>
                <span className="solver-page__strip-pill solver-page__strip-pill--accent">
                  {specifiedProducts.length} product{specifiedProducts.length !== 1 ? 's' : ''}
                </span>
              </div>
            </>
          )}
        </div>
        <div className="solver-page__strip-right">
          <button
            className="solver-page__back-btn"
            onClick={() => navigate('/generation')}
          >
            <span className="solver-page__back-label-long">BACK TO </span>GENERATION
          </button>
          <button
            className="solver-page__run-btn"
            onClick={handleSolve}
            disabled={solving}
          >
            {solving ? 'SOLVING...' : 'RUN SOLVER'}
            <Icon name="arrow_forward" />
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="solver-page__grid">
        {/* Left column */}
        <div className="solver-page__left-col">
          {specifiedProducts.length > 0 && (
            <CommittedProductsCard products={specifiedProducts} constraints={constraints} />
          )}
          <SourceRunCard run={sourceRun} />
          <ObjectiveSelector
            params={paramNames}
            objectiveParam={objectiveParam}
            objectiveSense={objectiveSense}
            onParamChange={setObjectiveParam}
            onSenseChange={setObjectiveSense}
          />
          <ConstraintList
            constraints={constraints}
            params={paramNames}
            onChange={setConstraints}
          />
          <MetricsPanel result={solveResult} />
          <SelectionsTable
            selections={solveResult?.selections}
            paramNames={paramNames}
          />
        </div>

        {/* Right column: Console */}
        <SolverConsole logs={logs} />
      </div>
    </div>
  );
}
