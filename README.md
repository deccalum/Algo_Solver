# GRIP Solve
> **G**enerator · (ca)**R**tesian · **I**nteger **P**rogramming

```
Define axes.  →  Generate every candidate.  →  Solve for the global optimum.
```

A general-purpose parametric optimisation platform. **Describe** a problem as typed parameter axes and constraints; the engine exhaustively enumerates the Cartesian product, enriches each item with computed fields, and hands the full catalog to a MILP solver that returns the globally optimal selection — *without you writing a single line of solver code*.

---

## The Core Engine
### 1 — Parametric Generation
A *template* declares $k$ independent parameter axes, each a distribution or discrete set over a range $[a_i, b_i]$. The engine constructs the full Cartesian product:

$$\Omega = P_1 \times P_2 \times \cdots \times P_k, \qquad |\Omega| = \prod_{i=1}^{k} |P_i|$$

*Influence rules* then wire axes together — e.g. efficiency modulates throughput before the catalog is finalised. The result is a typed catalog of $N$ candidate items, each carrying every computed field the solver needs.

### 2 — Combinatorial Optimisation (MILP)
Given the catalog, the solver formulates a **0-1 Integer Linear Programme**:

$$\max_{\mathbf{x} \in \{0,1\}^N} \; \mathbf{c}^\top \mathbf{x}$$

$$\text{subject to} \quad A\mathbf{x} \leq \mathbf{b}$$

where $x_i = 1$ means item $i$ is selected, $\mathbf{c}$ is the objective vector (e.g. profit, net savings, throughput), and $A\mathbf{x} \leq \mathbf{b}$ encodes user-defined constraints (budget, roof area, labour hours, warehouse capacity, …).

The solver runs SCIP via Google OR-Tools. Selections, generation runs, and solve runs are persisted to PostgreSQL and browsable in the Database page.

---

## Current Applications
### Inventory & Product Sourcing — *active*
The original use-case. Products are generated across price, weight, volume, and demand axes. The solver maximises profit subject to a budget and warehouse space constraint:

$$\max \sum_i \text{margin}_i \cdot x_i \qquad \text{s.t.} \quad \sum_i \text{cost}_i \cdot x_i \leq B, \quad \sum_i \text{vol}_i \cdot x_i \leq V$$

Supports custom distributions, logifier post-processing (realistic price clustering), specified/forced products, and a 30–90 day inventory simulation streamed live to the browser.

### Home Solar Advisor — *active proof-of-concept*
A consumer-facing solver searches every combination of:
| Axis               | Range                |
| ------------------ | -------------------- |
| Panel efficiency   | 15 – 23 %            |
| Panel cost         | \$0.20 – \$0.80 / W  |
| Annual degradation | 0.3 – 0.8 % / yr     |
| Battery capacity   | 0, 5, 10, 15, 20 kWh |
| Loan term          | cash, 10, 20, 25 yr  |
| Interest rate      | 3, 5, 7 % APR        |

≈ 3 750 configurations, solved in < 1 s. See [Solar math](#solar-math) for the financial model.

### Production Line Scheduling — *stub*
Template defined, solver constraints stubbed. Axes: labour hours, machine capacity, material cost, throughput. Planned objective: maximise throughput subject to weekly labour budget and per-cycle material spend.

---

## Multi-Use by Design
Every domain is a *template function* that returns a `Template` dataclass:
```python
@template
def solar_panel(cfg: SolarPanelConfig | None = None) -> Template:
    ...
    return Template(params=[eff, cpw, deg, bat, loan, rate], influences=[...], ...)

@template
def production_line(cfg: ProductionLineConfig | None = None) -> Template:
    ...
    return Template(params=[lab, mac, mat, tp], influences=[...], ...)
```

The FastAPI layer calls `from_template(tmpl)` → `solver.optimize(...)` identically for every domain. Adding a new use-case is: *write a template function, register it with `@template`*.

---

## Solar Math
**Peak Sun Hours** for a tilted, azimuth-rotated surface are computed by integrating the direct-beam irradiance $G(\omega)$ over the daylight hour-angle interval $[-\omega_s, +\omega_s]$:

$$G(\omega) = I_{sc} \cdot E_0 \left[ \sin\delta\sin\phi\cos\beta - \sin\delta\cos\phi\sin\beta\cos\gamma + \cos\delta\cos\omega(\cos\phi\cos\beta + \sin\phi\sin\beta\cos\gamma) + \cos\delta\sin\omega\sin\beta\sin\gamma \right]$$

where $\delta$ = declination, $\phi$ = latitude, $\beta$ = tilt, $\gamma$ = azimuth from south, $\omega$ = hour angle. Integrated with Simpson's rule over 48 steps and normalised by $1000 \; \text{W m}^{-2}$ to give PSH.

**Annual savings** for a system with $n$ panels, each of area $A$ and efficiency $\eta$:

$$S_{\text{annual}} = \underbrace{\eta \cdot \text{PSH} \cdot A \cdot n}_{\text{daily kWh}} \times 365 \times \left( \rho \cdot r_e + (1 - \rho) \cdot r_f \right)$$

where $\rho$ = self-consumption ratio (battery-adjusted), $r_e$ = electricity tariff, $r_f$ = feed-in tariff.

**Net lifetime value** (the solver's objective):

$$V_{\text{net}} = S_{\text{annual}} \cdot L \cdot \bar{d} - C_{\text{total}}$$

where $L$ = system lifetime, $\bar{d}$ = average degradation factor $= \dfrac{1 - (1 - r_d)^L}{L \cdot r_d}$, and $C_{\text{total}}$ is the total cost paid (upfront for cash, $n_m \cdot m$ for a loan of $n_m$ months at monthly payment $m$).

The solver's `select_one` constraint (`sum_le panel_count 1.0`) forces it to choose exactly one complete system configuration from the full catalog.

---

## The Protobuf Experiment
Early versions of this project used a **Java Spring Boot** service with **gRPC + Protocol Buffers** as the optimisation backend (commit history: `35e1914`, `b929652`). The `.proto` schemas defined `AlgoConfig`, `ProductEstimate`, and streaming `SolveResult` messages. gRPC gave typed, bi-directional streaming between the Java solver and a Node gateway.

The experiment validated that protobuf is a clean contract layer for solver I/O — field evolution is backwards-compatible and the schema doubles as documentation. However, in the current architecture the Python process already owns the solver, the database, and the HTTP API. Adding a gRPC hop would introduce latency and operational overhead with no benefit. The protobuf schema is archived in `docs/` for reference. If the solver is ever split into a dedicated microservice (see [Future](#future)), gRPC is the natural wire protocol.

---

## Stack
| Layer      | Technology                                        |
| ---------- | ------------------------------------------------- |
| Solver     | SCIP via Google OR-Tools (Python)                 |
| API        | FastAPI + SQLAlchemy + PostgreSQL                 |
| Frontend   | React 19 + Vite, plain CSS                        |
| Simulation | Python generator + NDJSON streaming to browser    |
| Infra      | Docker Compose (postgres, api, nginx+frontend)    |

```
frontend/          React SPA — Vite, React Router
python/
  generator.py     Cartesian generation engine + template registry
  solver.py        OR-Tools MILP wrapper
  solar.py         Solar irradiance / PSH physics
  simulation.py    Day-by-day inventory simulation (streaming)
  server/
    api.py         FastAPI routes
    db.py          SQLAlchemy models + migrations
```

### Running
```bash
./run.sh dev        # frontend (port 3000) + Python API (port 18000)
./run.sh docker-up  # full stack in Docker (postgres + api + nginx)
```

---

## Future
### Near-Term Features
- **Multi-period inventory LP** — rolling-horizon formulation: $\text{inv}_{t+1} = \text{inv}_t + \text{order}_t - \text{demand}_t$, optimised over the full horizon rather than one-shot per reorder day
- **Demand forecasting** — replace static `daily_rate` with a short moving average; add seasonal pattern detection (weekly/monthly cycle)
- **Safety stock** — derive reorder threshold from demand variance: $\text{ss} = z \cdot \sigma_d \cdot \sqrt{L}$ (z from service-level config, $L$ = lead time)
- **Solar simulation linkage** — post-solve daily energy simulation: generation vs. consumption, battery state-of-charge, actual vs. modelled savings
- **Force product selection** — hard-include path in the SCIP model (fix selected product, reduce constraint bounds)
- **Product implication constraints** — "if A then B" bundling rules as SCIP implication constraints
- **Weather/irradiance API** — replace clear-sky model ($\tau = 0.75$) with PVGIS / Open-Meteo historical data, gated by feature flag

### Python Backend — Towards Idiomatic Python
The backend is functional but several patterns can be made more Pythonic:
- **Generator-first simulation** — `run_simulation` currently builds a full list of `DaySnapshot` objects. Converting to a proper `Generator[DaySnapshot, None, None]` with `yield` allows the streaming endpoint to `yield` directly from the simulation loop without buffering the entire run in memory
- **`*args` / `**kwargs` propagation** — preset factory functions (`param()`, `influence()`, `segment()`) should accept and forward arbitrary kwargs to underlying distributions, removing the need for per-preset wrapper signatures
- **Context managers for DB sessions** — replace `Depends(get_db)` patterns with `with Session(engine) as db:` context managers in non-FastAPI code paths for cleaner resource management
- **Dataclass `__post_init__` validation** — config dataclasses (`SolarPanelConfig`, `ProductionLineConfig`) should validate ranges and raise `ValueError` early rather than propagating bad values into the generation loop
- **`functools.cache` on pure physics** — `annual_avg_psh`, `azimuth_gain_pct`, and similar deterministic functions called repeatedly for the same inputs should be memoized
- **`typing.Protocol` for template duck-typing** — instead of the `@template` decorator mutating a registry dict, define a `TemplateFactory(Protocol)` with `__call__(cfg) -> Template` so IDEs and mypy can reason about template callables

### Custom Solver — Decoupling from OR-Tools / SCIP
Google OR-Tools provides an excellent SCIP binding but comes with constraints that matter at scale:

- **No GPU execution path** — SCIP is a CPU-bound branch-and-bound algorithm; the OR-Tools Python bindings add GIL overhead on top
- **Limited branching control** — custom branching heuristics, node selection strategies, and cutting planes are not easily exposed through the OR-Tools API
- **Black-box LP relaxations** — accessing dual variables and reduced costs for warm-starting heuristics requires internal hooks OR-Tools does not expose

The plan is to implement a custom solver kernel in **C++** with the following design:
```
┌──────────────────────────────────┐
│  Python API layer (FastAPI)      │
│  — catalog JSON → solver RPC     │
└─────────────┬────────────────────┘
              │ shared memory / socket
┌─────────────▼────────────────────┐
│  C++ Solver Core                 │
│  ├─ LP relaxation (revised simplex, CUDA-accelerated basis updates)
│  ├─ Branch & Bound with custom node selector
│  ├─ Cutting planes (Gomory, cover cuts for 0-1 vars)
│  └─ GPU kernel: parallel reduced-cost evaluation on candidate columns
└──────────────────────────────────┘
```

**GPU acceleration target**: the most parallelisable part of B&B for this problem class is *evaluating the LP relaxation* at each node. The constraint matrix $A$ is dense for the Cartesian catalog structure, making batched matrix–vector products ($A\mathbf{x}$) ideal for CUDA. A CUDA kernel computing reduced costs across all $N$ columns in parallel would cut per-node LP solve time from $O(N \cdot m)$ sequential to $O(m)$ with $N$-wide SIMD.

**Milestones**:
1. Implement revised simplex in C++ with Eigen for the LP relaxation
2. CUDA kernel for basis-update and reduced-cost computation
3. Branch-and-bound shell with pluggable node selector and cut generator
4. Python `ctypes` / `pybind11` binding, drop-in replacement for `solver.optimize()`
