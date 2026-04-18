# Legacy Backend Feature Extract
Condensed, feature-first extraction of legacy backend behavior that is still useful for the current Python backend.

## Features
1. Demand modeling stack: combine business-context multipliers with stable price/size demand curves.
2. Transit optimization: assign shipping mode by eligibility and minimize transport cost.
3. Inventory policy stack: add deterministic auto-buy and startup stocking heuristics.
4. Realism models: standardize logistics, markup, and stock-availability primitives.
5. Config boundary: enforce strict adapter/validation with auto-span resolution.
6. Simulation fidelity: richer time-step state and optional pacing controller.
7. Async operations: add job lifecycle for long-running generation tasks.
8. Reporting: expose KPI rollups (revenue, COGS, profit, top products).
9. Batch fallback: support offline large-catalog optimization runs.
10. Business-hours queueing: gate and defer processing outside open hours.

### 1) Demand modeling stack (High)
Includes:
- Multi-factor demand modifier policy
- Demand curve as dedicated model unit

Legacy value:
- Combines business signals (seasonality, rating, pricing pressure, novelty, discounting) with a stable response curve.

Why still relevant:
- Current backend has flexible influences but no canonical demand policy stack.

#### Code normalized
```python
import math
import random

def demand_multiplier(*, season_factor: float, rating_factor: float, competitor_factor: float, is_new: bool, discounted: bool, budget_factor: float, noise: float) -> float:
    m = season_factor * rating_factor * competitor_factor * budget_factor * noise
    if is_new:
        m *= 1.35
    if discounted:
        m *= 1.50
    return round(max(0.1, m), 3)

def demand_score(price: float, size: float, *, base: float, p_scale: float, s_scale: float, p_sense: float, s_sense: float, noise: float, lo: float, hi: float) -> float:
    p = math.log10(max(1.0, price)) / math.log10(max(10.0, p_scale))
    s = math.log10(max(1.0, size)) / math.log10(max(10.0, s_scale))
    raw = base * math.exp(-(p_sense * p + s_sense * s))
    return max(lo, min(hi, raw * random.uniform(1.0 - noise, 1.0 + noise)))
```

Integration target:
- Add reusable demand policies in `python/generator.py` with template presets.

### 2) Transit mode assignment and cost minimization (High)
Legacy value:
- Explicit mode eligibility and cost comparison across courier/pallet/container.

Why still relevant:
- Current `python/solver.py` does not model transport mode choice.

#### Code normalized
```python
from dataclasses import dataclass
import math

@dataclass
class ShipMode:
    name: str
    capacity: float
    base_cost: float
    max_value_density: float
    min_weight: float

def choose_ship_mode(size: float, price: float, origin_factor: float, modes: list[ShipMode], weight_per_volume: float, eps: float = 1e-6):
    eligible = [m for m in modes if (price / max(size, eps) <= m.max_value_density and size * weight_per_volume >= m.min_weight)] or [modes[0]]
    best = min(eligible, key=lambda m: math.ceil(size / max(m.capacity, eps)) * m.base_cost * max(1.0, origin_factor))
    cost = math.ceil(size / max(best.capacity, eps)) * best.base_cost * max(1.0, origin_factor)
    return {"mode": best.name, "ship_cost": cost}
```

Integration target:
- Add item pre-processing in `python/generator.py` or request normalization in `python/server/api.py`.
- Add net-value objective option in `python/solver.py` that includes shipping cost.

### 3) Inventory policy stack (High)
Includes:
- Auto-buy reorder rules engine
- Heuristic initial stocking planner

Legacy value:
- Deterministic fallback behavior for replenishment and cold-start stocking.

Why still relevant:
- Current simulation is solver-first and lacks explicit per-SKU policy rules.

#### Code normalized
```python
from dataclasses import dataclass

@dataclass
class AutoBuyRule:
    sku: str
    threshold: int
    reorder_qty: int
    enabled: bool = True

def apply_auto_buy(stock: dict, rules: list[AutoBuyRule], unit_cost: dict, cash: float):
    ordered = {}
    for r in rules:
        if r.enabled and int(stock.get(r.sku, 0)) <= r.threshold:
            cost = unit_cost.get(r.sku, 0.0) * r.reorder_qty
            if cost <= cash:
                stock[r.sku] = int(stock.get(r.sku, 0)) + r.reorder_qty
                cash -= cost
                ordered[r.sku] = r.reorder_qty
    return stock, cash, ordered

def initial_stock_plan(items: list[dict], budget: float, space: float) -> dict[str, int]:
    ranked = sorted(items, key=lambda i: (i["retail"] - i["price"]) / max(i["volume"], 1e-9), reverse=True)
    plan, b, s = {}, budget, space
    for it in ranked:
        qty = max(0, min(int(b // max(it["price"], 1e-9)), int(s // max(it["volume"], 1e-9)), int(it.get("demand", 1) * 1.5)))
        if qty > 0:
            plan[it["id"]] = qty
            b -= qty * it["price"]
            s -= qty * it["volume"]
    return plan
```

Integration target:
- Add optional policy stage in `python/simulation.py` and a pre-solver initializer utility under `python/`.

### 4) Logistics, markup, and stock realism models (Medium)
Includes:
- Logistics difficulty penalty
- Markup curve with bounded stochasticity
- Stock availability with finite/infinite modes

Legacy value:
- Adds cost, margin, and availability realism beyond static attributes.

Why still relevant:
- Current backend can approximate this with influences, but lacks canonical presets.

#### Code normalized
```python
import math
import random

def logistics_difficulty(size: float, *, optimal: float, base_cost: float, penalty_factor: float, max_difficulty: float, min_log_size: float = 1e-3) -> float:
    d = math.log10(max(min_log_size, size)) - math.log10(max(min_log_size, optimal))
    return min(max_difficulty, base_cost + penalty_factor * (d ** 2))

def markup_rate(price: float, *, base_rate: float, scale: float, divisor: float, min_rate: float, max_rate: float, noise: float) -> float:
    rate = base_rate + (math.log10(max(1.0, price)) / max(divisor, 1e-6)) * scale
    return max(min_rate, min(max_rate, rate * random.uniform(1.0 - noise, 1.0 + noise)))

def sample_stock(price: float, size: float, *, base_stock: float, min_stock: int, inf_chance: float, inf_decay: float, inf_multiplier: float, inf_value: int, p_scale: float, s_scale: float, p_sense: float, s_sense: float, noise: float) -> int:
    p_inf = max(0.0, min(1.0, inf_chance * math.exp(-price / max(inf_decay, 1e-6)) * math.exp(-size / max(inf_decay * inf_multiplier, 1e-6))))
    if random.random() < p_inf:
        return inf_value
    p = math.log10(max(1.0, price)) / math.log10(max(10.0, p_scale))
    s = math.log10(max(1.0, size)) / math.log10(max(10.0, s_scale))
    stock = base_stock * math.exp(-(p_sense * p + s_sense * s)) * random.uniform(1.0 - noise, 1.0 + noise)
    return max(min_stock, int(stock))
```

Integration target:
- Add computed-field presets in `python/generator.py`; consider solver bound hooks for quantity-mode solving.

### 5) Strict config adapter boundary and auto-span resolution (Medium)
Legacy value:
- Centralized validation and nested config normalization with `auto` span support.

Why still relevant:
- Current backend lacks a single strict adapter path for complex user-supplied config.

#### Code normalized
```python
from dataclasses import dataclass

@dataclass
class ZoneCfg:
    mode: str
    span_share: float
    resolution: int
    bias: float
    step: float

def resolve_auto_spans(zones: list[dict]) -> list[dict]:
    fixed = sum(float(z["span_share"]) for z in zones if z.get("span_share") != "auto")
    n_auto = sum(1 for z in zones if z.get("span_share") == "auto")
    auto = (max(0.0, 1.0 - fixed) / n_auto) if n_auto else 0.0
    return [{**z, "span_share": auto if z.get("span_share") == "auto" else float(z["span_share"])} for z in zones]
```

Integration target:
- Add a strict request-to-config adapter in `python/server/api.py`.

### 6) Simulation control and state fidelity (Medium)
Includes:
- Forecast-oriented time-step state
- Time-speed simulation controller

Legacy value:
- Improves planning fidelity and enables deterministic pacing for demos/tests.

Why still relevant:
- Current loop is effective but lacks explicit advanced state and speed abstractions.

#### Code normalized
```python
from dataclasses import dataclass, field

@dataclass
class ItemState:
    on_hand: int
    inbound: list[tuple[int, int]]
    daily_rate: float
    unit_volume: float

@dataclass
class TimeStep:
    day: int
    stock: dict[str, ItemState]
    planned_order: dict[str, int] | None = None
    history: list["TimeStep"] = field(default_factory=list)

    def projected_space(self, target_day: int) -> float:
        return sum(max(0, int(s.on_hand + sum(q for d, q in s.inbound if self.day < d <= target_day) - s.daily_rate * (target_day - self.day))) * s.unit_volume for s in self.stock.values())

class SimClock:
    def __init__(self, speed: int = 4):
        self.speed = speed
        self.minute = 0

    def tick(self) -> int:
        self.minute += 1
        return self.minute
```

Integration target:
- Add optional advanced state and pacing mode in `python/simulation.py`.

### 7) Async generation job lifecycle (Medium)
Legacy value:
- Queue/run/complete/fail lifecycle for long-running generation.

Why still relevant:
- Current API is mostly synchronous request/response.

#### Code normalized
```python
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

def run_job(job_id: str, runner, repo):
    repo.update(job_id, status=JobStatus.RUNNING)
    try:
        repo.update(job_id, status=JobStatus.COMPLETED, output_text=runner())
    except Exception as exc:
        repo.update(job_id, status=JobStatus.FAILED, error_text=str(exc))
```

Integration target:
- Extend `python/server/api.py` with optional async endpoints and persisted job status.

### 8) Reporting and KPI aggregation (Medium)
Legacy value:
- Monthly rollups for revenue, COGS, gross/net profit, and top products.

Why still relevant:
- Current backend stores data but lacks a consolidated reporting surface.

#### Code normalized
```python
def monthly_summary(orders: list[dict], expenses: float = 0.0) -> dict:
    revenue = sum(o["total"] for o in orders)
    cogs = sum(i["wholesale"] * i["qty"] for o in orders for i in o["items"])
    sold = {}
    for o in orders:
        for i in o["items"]:
            sold[i["id"]] = sold.get(i["id"], 0) + i["qty"]
    return {
        "orders": len(orders),
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": revenue - cogs,
        "net_profit": revenue - cogs - expenses,
        "top_products": sorted(sold.items(), key=lambda kv: kv[1], reverse=True)[:5],
    }
```

Integration target:
- Add analytics endpoint in `python/server/api.py` backed by persisted solve/simulation data.

### 9) Batch optimization fallback path for extreme catalog sizes (Low)
Legacy value:
- Offline pipeline for very large CSV-based runs.

Why still relevant:
- Useful as debug and stress-test fallback when API-first flow is not ideal.

#### Code normalized
```python
def optimize_batch(rows: list[dict], budget: float, space: float) -> dict:
    items = normalize_rows(rows)
    request = build_request(items, budget=budget, space=space)
    result = run_solver(request)
    return {
        "status": result["status"],
        "selected": sort_by_score(result["selected"]),
        "stats": build_timing_and_constraint_summary(result),
    }
```

Integration target:
- Optional utility script under `python/` for offline replay and benchmark runs.

### 10) Business-hours order gating with deferred queue (Low)
Legacy value:
- Defer processing outside operating hours.

Why still relevant:
- Adds operational realism and throughput bottleneck testing.

#### Code normalized
```python
def route_order(order: dict, is_open: bool, queue: list[dict], processed: list[dict]):
    (processed if is_open else queue).append(order)
    return queue, processed
```

Integration target:
- Optional extension in `python/simulation.py` if business-hours realism is required.

## Migration Priority

- High: Demand modeling stack
- High: Transit mode assignment and cost minimization
- High: Inventory policy stack
- Medium: Logistics, markup, and stock realism models
- Medium: Strict config adapter boundary and auto-span resolution
- Medium: Simulation control and state fidelity
- Medium: Async generation job lifecycle
- Medium: Reporting and KPI aggregation
- Low: Batch optimization fallback path for extreme catalog sizes
- Low: Business-hours order gating with deferred queue
