import json
from uuid import UUID

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

import python.generator as generator
import python.solver as solver
from python.main import NumpyEncoder, total_count, resolve_specs, COMBINATION_LIMIT
from python.server.db import (
    get_db, engine, init_db,
    GenerationRun, GeneratedItem, SolveRun, SolveSelection,
    validate_table_name, build_filter_where_clause,
)


# -- Custom JSON response for numpy scalars --
class NumpyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, cls=NumpyEncoder).encode("utf-8")


# -- App --
app = FastAPI(title="Algo Solver API", default_response_class=NumpyJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# -- Admin --
@app.post("/api/admin/restart")
def restart_endpoint():
    """Restart the API server process (re-exec with the same argv)."""
    import os, sys, threading

    def _restart():
        import time
        time.sleep(0.4)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    threading.Thread(target=_restart, daemon=True).start()
    return {"status": "restarting"}


# -- Pydantic Schemas --
class ParamSpecSchema(BaseModel):
    name: str
    dist: str = "uniform"
    min: float | None = None
    max: float | None = None
    values: list | None = None
    dist_kwargs: dict = Field(default_factory=dict)

class InfluenceSchema(BaseModel):
    source: str
    target: str
    fn: str
    kwargs: dict = Field(default_factory=dict)

class ConstraintSchema(BaseModel):
    name: str
    kind: str
    param_name: str
    bound: float

class LogifierConfig(BaseModel):
    enabled: bool = True
    density_floor: float = 50.0
    density_ceiling: float = 20_000.0
    price_per_litre_ceiling: float = 5_000_000.0
    price_size_threshold: float = 0.0005

class CountRequest(BaseModel):
    template: str | None = None
    params: list[ParamSpecSchema] = Field(default_factory=list)
    influences: list[InfluenceSchema] = Field(default_factory=list)
    overrides: dict = Field(default_factory=dict)
    logifier: LogifierConfig | None = None

class GenerateRequest(BaseModel):
    template: str | None = None
    params: list[ParamSpecSchema] = Field(default_factory=list)
    influences: list[InfluenceSchema] = Field(default_factory=list)
    overrides: dict = Field(default_factory=dict)
    limit: int = COMBINATION_LIMIT
    logifier: LogifierConfig | None = None

class SpecifiedProductSchema(BaseModel):
    name: str = ""
    price: float
    amount: int
    volume: float
    weight: float | None = None

class SolveRequestSchema(BaseModel):
    template: str | None = None
    params: list[ParamSpecSchema] = Field(default_factory=list)
    influences: list[InfluenceSchema] = Field(default_factory=list)
    overrides: dict = Field(default_factory=dict)
    generation_run_id: UUID | None = None
    constraints: list[ConstraintSchema] = Field(default_factory=list)
    objective_param: str = "demand"
    objective_sense: str = "maximize"
    limit: int = COMBINATION_LIMIT
    specified_products: list[SpecifiedProductSchema] = Field(default_factory=list)

class SimConfigSchema(BaseModel):
    time_horizon:      int   = 30
    space_capacity:    float = 500.0
    space_buffer:      float = 0.15
    lead_time:         int   = 3
    budget:            float = 50_000.0
    reorder_threshold: float = 0.25

class SimulateRequest(BaseModel):
    solve_id: UUID
    config:   SimConfigSchema = Field(default_factory=SimConfigSchema)


# -- Helpers --
def _build_filter(base_filter_fn, logifier_cfg):
    """Compose base filter with logifier if enabled."""
    if not (logifier_cfg and logifier_cfg.enabled):
        return base_filter_fn
    log_fn = generator.logifier(
        density_floor=logifier_cfg.density_floor,
        density_ceiling=logifier_cfg.density_ceiling,
        price_per_litre_ceiling=logifier_cfg.price_per_litre_ceiling,
        price_size_threshold=logifier_cfg.price_size_threshold,
    )
    if base_filter_fn:
        return lambda r, _b=base_filter_fn, _l=log_fn: _b(r) and _l(r)
    return log_fn

def _to_resolve_dict(req) -> dict:
    """Convert Pydantic request to the dict format resolve_specs() expects."""
    if req.template:
        return {"template": req.template, "overrides": getattr(req, "overrides", {})}
    return {
        "params": [p.model_dump() for p in req.params],
        "influences": [i.model_dump() for i in req.influences],
    }

def _serialize_params(specs: list) -> list[dict]:
    result = []
    for s in specs:
        d = {
            "name": s.name,
            "dist": s.dist.__name__,
            "min": s.min, "max": s.max,
            "dist_kwargs": s.dist_kwargs,
        }
        if s.values is not None:
            d["values"] = s.values
        result.append(d)
    return result

def _serialize_influences(rules: list) -> list[dict]:
    return [
        {"source": r.source, "target": r.target, "fn": r.fn.__name__, "kwargs": r.kwargs}
        for r in rules
    ]

def _template_info(name: str, tmpl) -> dict:
    return {
        "name": name,
        "params": [
            {
                "name": p.name,
                "dist": p.dist.__name__,
                "min": p.min, "max": p.max,
                "dist_kwargs": p.dist_kwargs,
            }
            for p in tmpl.params
        ],
        "influences": [
            {"source": r.source, "target": r.target, "fn": r.fn.__name__}
            for r in tmpl.influences
        ],
        "constraints": [
            {"name": c.name, "kind": c.kind, "param_name": c.param_name, "bound": c.bound}
            for c in tmpl.constraints
        ],
        "objective_param": tmpl.objective_param,
        "objective_sense": tmpl.objective_sense,
    }


# ==================== ENDPOINTS ====================

# -- Health --
@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


# -- Templates --
@app.get("/api/templates")
def list_templates_endpoint():
    result = []
    for name in generator.list_templates():
        tmpl = generator.get_template(name)
        info = _template_info(name, tmpl)
        info["combination_count"] = total_count(*tmpl.params)
        result.append(info)
    return result

@app.get("/api/templates/{name}")
def get_template_endpoint(name: str):
    try:
        tmpl = generator.get_template(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    info = _template_info(name, tmpl)
    info["combination_count"] = total_count(*tmpl.params)
    return info


# -- Count --
@app.post("/api/count")
def count_combinations(req: CountRequest):
    specs, influences, filter_fn, template_name = resolve_specs(_to_resolve_dict(req))
    pre_filter = total_count(*specs)

    if pre_filter > COMBINATION_LIMIT:
        return {"count": pre_filter, "limit": COMBINATION_LIMIT, "ok": False}

    # Generate all rows (without filter) so we can apply scoring
    all_items = generator.cartesian_generator(*specs, influences=influences, filter_fn=filter_fn, template_name=template_name)

    if req.logifier and req.logifier.enabled:
        # Use logifier_score for a deterministic expected-count (no randomness)
        score_fn = generator.logifier_score(
            density_floor=req.logifier.density_floor,
            density_ceiling=req.logifier.density_ceiling,
            price_per_litre_ceiling=req.logifier.price_per_litre_ceiling,
            price_size_threshold=req.logifier.price_size_threshold,
        )
        total = round(sum(score_fn(row) for row in all_items))
    else:
        total = len(all_items)

    return {"count": total, "limit": COMBINATION_LIMIT, "ok": total <= COMBINATION_LIMIT}


# -- Generate --

@app.post("/api/generate")
def generate(req: GenerateRequest, db: Session = Depends(get_db)):
    specs, influences, filter_fn, template_name = resolve_specs(_to_resolve_dict(req))
    filter_fn = _build_filter(filter_fn, req.logifier)
    total = total_count(*specs)

    if total > req.limit:
        raise HTTPException(
            status_code=400,
            detail=f"{total:,} combinations exceeds limit of {req.limit:,}",
        )

    items = generator.cartesian_generator(*specs, influences=influences, filter_fn=filter_fn, template_name=template_name)

    run = GenerationRun(
        template_name=template_name,
        params=_serialize_params(specs),
        influences=_serialize_influences(influences),
        item_count=len(items),
    )
    db.add(run)
    db.flush()

    db_items = [GeneratedItem(run_id=run.id, item_id=item["id"], data=item) for item in items]
    db.add_all(db_items)
    db.commit()

    return {
        "run_id": str(run.id),
        "template_name": template_name,
        "item_count": len(items),
    }


# -- Solve --
@app.post("/api/solve")
def solve(req: SolveRequestSchema, db: Session = Depends(get_db)):
    if req.generation_run_id:
        gen_run = db.get(GenerationRun, req.generation_run_id)
        if not gen_run:
            raise HTTPException(status_code=404, detail="Generation run not found")
        db_items = (
            db.query(GeneratedItem)
            .filter(GeneratedItem.run_id == req.generation_run_id)
            .all()
        )
        items = [item.data for item in db_items]
        generation_run_id = req.generation_run_id
        template_name = gen_run.template_name
    else:
        specs, influences, filter_fn, template_name = resolve_specs(
            _to_resolve_dict(req)
        )
        total = total_count(*specs)
        if total > req.limit:
            raise HTTPException(
                status_code=400,
                detail=f"{total:,} exceeds limit of {req.limit:,}",
            )

        items = generator.cartesian_generator(
            *specs, influences=influences, filter_fn=filter_fn,
            template_name=template_name,
        )

        gen_run = GenerationRun(
            template_name=template_name,
            params=_serialize_params(specs),
            influences=_serialize_influences(influences),
            item_count=len(items),
        )
        db.add(gen_run)
        db.flush()

        db_items = [
            GeneratedItem(run_id=gen_run.id, item_id=item["id"], data=item)
            for item in items
        ]
        db.add_all(db_items)
        db.flush()
        generation_run_id = gen_run.id

    # Build solver request — deduct committed products from constraint bounds.
    # Each specified product's price/volume/weight is matched against the
    # constraint's param_name, reducing the effective bound pre-solve.
    constraints = []
    for c in req.constraints:
        bound = c.bound
        for sp in req.specified_products:
            field_value = getattr(sp, c.param_name, None)
            if field_value is not None:
                bound = max(0.0, bound - field_value * sp.amount)
        constraints.append(solver.ConstraintSpec(
            name=c.name,
            kind=solver.ConstraintKind(c.kind),
            param_name=c.param_name,
            bound=bound,
        ))
    solve_request = solver.SolveRequest(
        items=items,
        constraints=constraints,
        objective_param=req.objective_param,
        objective_sense=solver.Sense(req.objective_sense),
    )
    result = solver.optimize(solve_request)

    # Persist solve run
    solve_run = SolveRun(
        generation_run_id=generation_run_id,
        constraints=[c.model_dump() for c in req.constraints],
        objective_param=req.objective_param,
        objective_sense=req.objective_sense,
        objective_value=result.objective_value,
        selected_count=len(result.selections),
    )
    db.add(solve_run)
    db.flush()

    # Map selected items to DB row IDs
    item_id_map = {di.item_id: di.id for di in db_items}
    selections = []
    for sel in result.selections:
        db_item_pk = item_id_map.get(sel["id"])
        if db_item_pk is not None:
            selections.append(
                SolveSelection(solve_run_id=solve_run.id, item_id=db_item_pk)
            )
    db.add_all(selections)
    db.commit()

    return {
        "solve_id": str(solve_run.id),
        "generation_run_id": str(generation_run_id),
        "objective_value": result.objective_value,
        "selected_count": len(result.selections),
        "total_generated": len(items),
    }


# -- Run History --
@app.get("/api/runs")
def list_runs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    runs = (
        db.query(GenerationRun)
        .order_by(GenerationRun.created_at.desc())
        .offset(offset).limit(limit).all()
    )
    return [
        {
            "id": str(r.id),
            "template_name": r.template_name,
            "item_count": r.item_count,
            "created_at": r.created_at.isoformat(),
            "params": r.params,
        }
        for r in runs
    ]

@app.get("/api/runs/{run_id}")
def get_run(run_id: UUID, db: Session = Depends(get_db)):
    run = db.get(GenerationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": str(run.id),
        "template_name": run.template_name,
        "item_count": run.item_count,
        "created_at": run.created_at.isoformat(),
        "params": run.params,
        "influences": run.influences,
        "solve_runs": [
            {
                "id": str(s.id),
                "objective_value": s.objective_value,
                "selected_count": s.selected_count,
                "created_at": s.created_at.isoformat(),
            }
            for s in run.solve_runs
        ],
    }

@app.get("/api/runs/{run_id}/items")
def get_run_items(
    run_id: UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    run = db.get(GenerationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    items = (
        db.query(GeneratedItem)
        .filter(GeneratedItem.run_id == run_id)
        .offset(offset).limit(limit).all()
    )
    return {
        "run_id": str(run_id),
        "total": run.item_count,
        "offset": offset,
        "limit": limit,
        "items": [{"id": i.id, "item_id": i.item_id, "data": i.data} for i in items],
    }

# -- Solve History --
@app.get("/api/solves")
def list_solves(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    solves = (
        db.query(SolveRun)
        .order_by(SolveRun.created_at.desc())
        .offset(offset).limit(limit).all()
    )
    return [
        {
            "id": str(s.id),
            "generation_run_id": str(s.generation_run_id),
            "objective_param": s.objective_param,
            "objective_sense": s.objective_sense,
            "objective_value": s.objective_value,
            "selected_count": s.selected_count,
            "created_at": s.created_at.isoformat(),
        }
        for s in solves
    ]

@app.get("/api/solves/{solve_id}")
def get_solve(solve_id: UUID, db: Session = Depends(get_db)):
    solve_run = db.get(SolveRun, solve_id)
    if not solve_run:
        raise HTTPException(status_code=404, detail="Solve run not found")
    selections = (
        db.query(SolveSelection)
        .filter(SolveSelection.solve_run_id == solve_id)
        .all()
    )
    return {
        "id": str(solve_run.id),
        "generation_run_id": str(solve_run.generation_run_id),
        "constraints": solve_run.constraints,
        "objective_param": solve_run.objective_param,
        "objective_sense": solve_run.objective_sense,
        "objective_value": solve_run.objective_value,
        "selected_count": solve_run.selected_count,
        "created_at": solve_run.created_at.isoformat(),
        "selections": [
            {"item_id": s.item_id, "data": s.item.data} for s in selections
        ],
    }


# -- Solar --
@app.get("/api/solar/psh")
def solar_psh_endpoint(
    lat:     float       = Query(...,          description="Latitude in degrees (-90 to +90)"),
    tilt:    float|None  = Query(default=None, description="Panel tilt from horizontal in degrees. Default: abs(lat) — optimal annual tilt."),
    azimuth: float|None  = Query(default=None, description="Panel azimuth from equator-facing direction. 0 = south (NH), +90 = west, −90 = east. Default: 0 (optimal)."),
    date:    str|None    = Query(default=None, description="ISO date YYYY-MM-DD. Default: today."),
):
    """
    Compute daily peak sun hours for a given location, panel orientation, and date.

    Returns the PSH for the requested date, the annual average, the seasonal
    (winter/summer) extremes, the optimal azimuth label, and (when azimuth is
    non-optimal) the percentage yield lost vs. equator-facing orientation.
    """
    from datetime import date as _date
    from python.solar import (
        peak_sun_hours, annual_avg_psh, sunlight_range_for_lat,
        azimuth_gain_pct, optimal_azimuth_label,
    )

    on_date = None
    if date:
        try:
            on_date = _date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date: {date!r} — use YYYY-MM-DD")

    tilt_used     = tilt if tilt is not None else abs(lat)
    azimuth_used  = azimuth if azimuth is not None else 0.0
    psh           = peak_sun_hours(lat, tilt, azimuth, on_date)
    avg           = annual_avg_psh(lat, tilt, azimuth)
    season_min, season_max = sunlight_range_for_lat(lat, tilt, azimuth)
    gain_pct      = azimuth_gain_pct(lat, tilt, azimuth_used)
    opt_label     = optimal_azimuth_label(lat)

    result = {
        "lat":              lat,
        "tilt_used":        tilt_used,
        "azimuth_used":     azimuth_used,
        "optimal_azimuth":  opt_label,
        "date":             (on_date or _date.today()).isoformat(),
        "psh":              psh,
        "annual_avg_psh":   avg,
        "seasonal_min_psh": season_min,
        "seasonal_max_psh": season_max,
    }
    if gain_pct > 0.0:
        result["azimuth_gain_pct"] = gain_pct
    return result


# -- Solar Solve --
class SolarSolveRequest(BaseModel):
    # Location
    lat:                  float
    tilt:                 float | None = None    # None → abs(lat)
    azimuth:              float | None = None    # None → 0° (equator-facing)
    # Financial inputs (battery/loan/rate are Cartesian axes — explored by solver)
    electricity_rate:     float        = 0.28   # $/kWh current tariff
    feed_in_rate:         float        = 0.08   # $/kWh sell-back
    upfront_budget:       float        = 10_000.0  # max system cost (cash or loan principal)
    max_monthly:          float | None = None   # optional: cap on monthly loan payment
    battery_cost_per_kwh: float        = 800.0  # $/kWh for battery storage hardware
    # System
    roof_area_m2:         float        = 30.0
    panel_area_m2:        float        = 1.7
    system_lifetime:      int          = 25
    # Household
    daily_kwh:            float        = 10.0   # household daily consumption kWh


@app.post("/api/solar/solve")
def solar_solve_endpoint(req: SolarSolveRequest, db: Session = Depends(get_db)):
    """
    Consumer-facing solar system solver.

    Generates all combinations of:
      panel tier (efficiency × cost_per_watt × degradation_rate)
      × battery size (0, 5, 10, 15, 20 kWh)
      × financing (loan term 0/10/20/25 yr at 3/5/7% interest)

    For each combination the enricher computes system_cost, monthly_payment,
    and net_value = lifetime_savings − total_cost_paid.

    The SCIP solver picks the single system (select_one constraint) that
    maximises net_value subject to the budget and optional monthly cap.
    """
    from python.solar import annual_avg_psh, azimuth_gain_pct, optimal_azimuth_label
    from python.generator import SolarPanelConfig, get_template, from_template
    from python.solver import SolveRequest as SReq, ConstraintSpec, ConstraintKind, Sense
    import math

    sunlight_hours = annual_avg_psh(req.lat, req.tilt, req.azimuth)
    n_panels       = max(1, math.floor(req.roof_area_m2 / req.panel_area_m2))

    cfg = SolarPanelConfig(
        sunlight_hours_value  = sunlight_hours,
        electricity_rate      = req.electricity_rate,
        feed_in_rate          = req.feed_in_rate,
        panel_area_m2         = req.panel_area_m2,
        system_lifetime_years = req.system_lifetime,
        n_panels              = n_panels,
        daily_kwh             = req.daily_kwh,
        battery_cost_per_kwh  = req.battery_cost_per_kwh,
        lat                   = req.lat,
        tilt                  = req.tilt,
        azimuth               = req.azimuth,
    )
    tmpl  = get_template("solar_panel", cfg)
    items = from_template(tmpl)

    if not items:
        raise HTTPException(status_code=422, detail="No viable configurations generated for these inputs.")

    # Persist generation run
    gen_run = GenerationRun(
        template_name="solar_panel",
        params=[{"name": p.name, "min": p.min, "max": p.max, "values": p.values} for p in tmpl.params],
        influences=[],
        item_count=len(items),
    )
    db.add(gen_run)
    db.flush()
    db_items = [GeneratedItem(run_id=gen_run.id, item_id=item["id"], data=item) for item in items]
    db.add_all(db_items)
    db.flush()

    # Constraints: budget on upfront system cost; select_one forces single pick
    constraints = [
        ConstraintSpec("budget",     ConstraintKind.SUM_LE, "system_cost",  req.upfront_budget),
        ConstraintSpec("select_one", ConstraintKind.SUM_LE, "panel_count",  1.0),
    ]
    if req.max_monthly is not None and req.max_monthly > 0:
        constraints.append(
            ConstraintSpec("monthly", ConstraintKind.SUM_LE, "monthly_payment", req.max_monthly)
        )

    result = solver.optimize(SReq(
        items           = items,
        constraints     = constraints,
        objective_param = "net_value",
        objective_sense = Sense.MAXIMIZE,
    ))

    # Persist solve run + selections
    solve_run = SolveRun(
        generation_run_id = gen_run.id,
        constraints       = [{"name": c.name, "kind": c.kind.value,
                               "param_name": c.param_name, "bound": c.bound}
                              for c in constraints],
        objective_param   = "net_value",
        objective_sense   = "maximize",
        objective_value   = result.objective_value,
        selected_count    = len(result.selections),
    )
    db.add(solve_run)
    db.flush()

    item_id_map = {di.item_id: di.id for di in db_items}
    db.add_all([
        SolveSelection(solve_run_id=solve_run.id, item_id=item_id_map[sel["id"]])
        for sel in result.selections
        if sel["id"] in item_id_map
    ])
    db.commit()

    # Build response — pull financials from the selected item (solver picks exactly 1)
    selected = result.selections
    azimuth_used = req.azimuth if req.azimuth is not None else 0.0
    gain_pct     = azimuth_gain_pct(req.lat, req.tilt, azimuth_used)

    sel = selected[0] if selected else {}
    system_cost    = sel.get("system_cost", 0)
    annual_savings = sel.get("annual_savings", 0)
    payback_years  = round(system_cost / annual_savings, 1) if annual_savings > 0 else None

    response: dict = {
        "solve_id":           str(solve_run.id),
        "generation_run_id":  str(gen_run.id),
        "objective_value":    result.objective_value,
        "selected_count":     len(selected),
        "total_generated":    len(items),
        "sunlight_hours_used": round(sunlight_hours, 2),
        "n_panels":           n_panels,
        "azimuth_used":       azimuth_used,
        "optimal_azimuth":    optimal_azimuth_label(req.lat),
        "upfront_budget":     req.upfront_budget,
        "system_cost":        round(system_cost, 2),
        "annual_savings":     round(annual_savings, 2),
        "payback_years":      payback_years,
        "system_lifetime":    req.system_lifetime,
        "selections":         selected,
    }
    if gain_pct > 0.0:
        response["azimuth_gain_pct"] = gain_pct

    # Top-3 alternatives ranked by net_value (excluding the winner)
    winner_id = sel.get("id") if sel else None
    sorted_items = sorted(items, key=lambda x: x.get("net_value", 0), reverse=True)
    response["alternatives"] = [x for x in sorted_items if x.get("id") != winner_id][:3]

    return response


# -- Simulation --
@app.post("/api/simulate/run")
def run_simulation_endpoint(req: SimulateRequest, db: Session = Depends(get_db)):
    solve_run = db.get(SolveRun, req.solve_id)
    if not solve_run:
        raise HTTPException(status_code=404, detail="Solve run not found")

    selections = (
        db.query(SolveSelection)
        .filter(SolveSelection.solve_run_id == req.solve_id)
        .all()
    )
    items = [s.item.data for s in selections]
    if not items:
        raise HTTPException(status_code=400, detail="No selected items in this solve run")

    from python.simulation import run_simulation, SimConfig
    config    = SimConfig(**req.config.model_dump())
    snapshots = run_simulation(items, config)

    return {
        "solve_id":    str(req.solve_id),
        "time_horizon": config.time_horizon,
        "days": [
            {
                "day":             s.day,
                "stock":           s.stock,
                "units_sold":      s.units_sold,
                "units_received":  s.units_received,
                "units_ordered":   s.units_ordered,
                "space_used":      s.space_used,
                "space_available": s.space_available,
                "action":          s.action,
                "log_level":       s.log_level,
                "log_text":        s.log_text,
            }
            for s in snapshots
        ],
    }


@app.post("/api/simulate/stream")
def stream_simulation(req: SimulateRequest, db: Session = Depends(get_db)):
    solve_run = db.get(SolveRun, req.solve_id)
    if not solve_run:
        raise HTTPException(status_code=404, detail="Solve run not found")

    selections = (
        db.query(SolveSelection)
        .filter(SolveSelection.solve_run_id == req.solve_id)
        .all()
    )
    items = [s.item.data for s in selections]
    if not items:
        raise HTTPException(status_code=400, detail="No selected items in this solve run")

    from python.simulation import run_simulation_iter, SimConfig
    config = SimConfig(**req.config.model_dump())

    def generate():
        yield json.dumps({
            "type": "meta",
            "solve_id": str(req.solve_id),
            "time_horizon": config.time_horizon,
            "item_count": len(items),
        }) + "\n"
        for snap in run_simulation_iter(items, config):
            yield json.dumps({
                "type":            "day",
                "day":             snap.day,
                "stock":           snap.stock,
                "units_sold":      snap.units_sold,
                "units_received":  snap.units_received,
                "units_ordered":   snap.units_ordered,
                "space_used":      snap.space_used,
                "space_available": snap.space_available,
                "action":          snap.action,
                "log_level":       snap.log_level,
                "log_text":        snap.log_text,
            }) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# -- Database Browser (ported from legacy) --
@app.get("/api/database/tables")
def get_tables(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )).fetchall()
    result = []
    for (table_name,) in rows:
        count = db.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar()
        result.append({"name": table_name, "row_count": count})
    return result

@app.get("/api/database/tables/{name}/schema")
def get_table_schema(name: str, db: Session = Depends(get_db)):
    try:
        validate_table_name(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    rows = db.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :name "
        "ORDER BY ordinal_position"
    ), {"name": name}).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Table {name!r} not found")
    return [{"column": r[0], "type": r[1]} for r in rows]

@app.get("/api/database/tables/{name}/data")
def get_table_data(
    name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    filters: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        validate_table_name(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    where_clause = ""
    params: dict = {}
    if filters:
        try:
            filter_model = json.loads(filters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid filters JSON")
        try:
            where_clause, params = build_filter_where_clause(filter_model)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    count_sql = f'SELECT COUNT(*) FROM "{name}" {where_clause}'
    total = db.execute(text(count_sql), params).scalar()

    data_sql = (
        f'SELECT * FROM "{name}" {where_clause} '
        f"LIMIT :_limit OFFSET :_offset"
    )
    params["_limit"] = limit
    params["_offset"] = offset
    rows = db.execute(text(data_sql), params)
    columns = list(rows.keys())
    data = [dict(zip(columns, row)) for row in rows.fetchall()]
    
    return {"total": total, "offset": offset, "limit": limit, "data": data}
