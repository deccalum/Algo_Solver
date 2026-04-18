# generator.py — Cartesian Generator
# ──────────────────────────────────────────────────────────────────────────────
from dataclasses import dataclass, field
from typing import Callable, Any
import itertools
import random
import numpy as np
import builtins

# ── Auto-registration ──────────────────────────────────────────────────────────
# Both distributions and influence functions follow the same decorator pattern.
# Any custom function decorated with @distribution or @influence_fn is
# automatically available by name — no manual registry entry needed.
#
# @distribution accepts an optional count_fn so each dist can report its output
# size cheaply, without generating values. Used by the counter in main.py.
# count_fn signature: (min, max, **kwargs) → int

DIST_REGISTRY  = {}
COUNT_REGISTRY = {}
INFL_REGISTRY  = {}
TEMPLATE_REGISTRY = {}

ID = "id"       # shared field key on generated rows — used by solver + main

def distribution(fn=None, *, count_fn=None):
    """Register a distribution function.

    count_fn: optional (min, max, **dist_kwargs) → int for fast axis size.
              If omitted, param_count will call the distribution directly.
    """
    def register(f):
        DIST_REGISTRY[f.__name__]  = f
        if count_fn is not None:
            COUNT_REGISTRY[f.__name__] = count_fn
        return f
    return register(fn) if fn is not None else register

def influence_fn(fn):
    INFL_REGISTRY[fn.__name__] = fn
    return fn


# ── 1. Distribution Algorithms ─────────────────────────────────────────────────
# Signature: (min, max, **kwargs) → list[float]
@distribution
def uniform(min, max, resolution=10, **kwargs):
    return np.linspace(min, max, resolution).tolist()

@distribution
def gaussian(min, max, resolution=10, midpoint=None, std=None, skew=0.0, **kwargs):
    """Bell-curve distribution over [min, max].

    midpoint : center of the distribution (default: midpoint of range)
    std      : standard deviation (default: range/6, puts ~99.7% within range)
    skew     : shape parameter for asymmetry.  0 = symmetric.
               > 0 = right tail (mass shifted left).  < 0 = left tail.
               Uses folded-normal method: X = δ|U₁| + √(1-δ²)U₂, scaled.
    """
    mean = midpoint if midpoint is not None else (min + max) / 2
    if std is None:
        std = (max - min) / 6
    if skew == 0.0:
        samples = np.random.normal(mean, std, resolution * 4)
    else:
        delta = skew / np.sqrt(1.0 + skew ** 2)
        u1 = np.abs(np.random.normal(0, 1, resolution * 4))
        u2 = np.random.normal(0, 1, resolution * 4)
        z = delta * u1 + np.sqrt(1.0 - delta ** 2) * u2
        samples = mean + std * z
    return sorted(np.clip(samples, min, max).tolist())[:resolution]

@distribution
def power(min, max, resolution=10, bias=2.0, **kwargs):
    """Skewed distribution over [min, max].

    bias > 1 : values cluster toward min  (e.g. bias=2 → many cheap, few expensive)
    bias = 1 : uniform spacing
    bias < 1 : values cluster toward max  (e.g. bias=0.5 → few cheap, many expensive)
    """
    t = np.linspace(0, 1, resolution)
    return [min + (max - min) * (ti ** bias) for ti in t]

@distribution
def geometric(min, max, resolution=10, **kwargs):
    safe_min = builtins.max(min, 1e-9)
    ratio    = (max / safe_min) ** (1 / (resolution - 1))
    return [safe_min * ratio ** i for i in range(resolution)]

def _step_count(mn, mx, step=1.0, **kw):
    return int((mx - mn) / step) + 1

@distribution(count_fn=_step_count)
def step(min, max, step=1.0, **kwargs):
    return [float(v) for v in np.arange(min, max + step, step)]

@dataclass
class Segment:
    """One range + distribution within a segmented axis.

    Args:
        min, max : bounds for this segment
        dist     : distribution function (default: step)
        kwargs   : extra kwargs forwarded to the dist (e.g. step=2.5, bias=0.5)
    """
    min:    float
    max:    float
    dist:   Callable[..., list] = field(default_factory=lambda: step)
    kwargs: dict                = field(default_factory=dict)

@distribution
def segmented(min, max, segments=None, **kwargs) -> list[float]:
    """Concatenate values from multiple sub-distributions, one per Segment.

    ``min`` / ``max`` are accepted to satisfy the ParamSpec interface but are
    ignored when ``segments`` is provided — each Segment carries its own bounds.

    ``segments`` accepts both ``Segment`` objects and plain dicts (as sent from
    the API / frontend)::

        # Python
        segments=[Segment(1, 25, step, {"step": 1}), ...]

        # JSON / dict (from API)
        segments=[{"min": 1, "max": 25, "dist": "step", "kwargs": {"step": 1}}, ...]
    """
    if not segments:
        return step(min, max, **kwargs)

    result = []
    seen   = set()
    for seg in segments:
        if isinstance(seg, dict):
            s_min, s_max = seg.get("min", min), seg.get("max", max)
            s_dist       = seg.get("dist", "step")
            s_kwargs     = seg.get("kwargs", {})
        else:
            s_min, s_max = seg.min, seg.max
            s_dist, s_kwargs = seg.dist, seg.kwargs
        fn = resolve_dist(s_dist)
        for v in fn(s_min, s_max, **s_kwargs):
            rounded = round(v, 10)
            if rounded not in seen:
                seen.add(rounded)
                result.append(v)
    return sorted(result)



# ── 2. Influence Functions ─────────────────────────────────────────────────────
# Signature: (source, target, **kwargs) → new_target
@influence_fn
def scale(source, target, factor=1.0, **kwargs):
    """Multiply target by a constant factor (source ignored, kept for registry compat)."""
    return target * factor

@influence_fn
def offset(source, target, factor=0.0, **kwargs):
    return target + source * factor

@influence_fn
def clamp(source, target, ratio=0.2, **kwargs):
    lo, hi = source * (1 - ratio), source * (1 + ratio)
    return builtins.max(lo, builtins.min(hi, target))

@influence_fn
def normalized_inverse(source, target, source_min=0.0, source_max=1.0, strength=0.8, floor=None, **kwargs):
    """Reduce target as source increases, normalized over [source_min, source_max].

    At source_min → target unchanged.
    At source_max → target *= (1 - strength).
    Optional floor clamps the result to a minimum value.
    """
    norm   = (source - source_min) / builtins.max(source_max - source_min, 1e-10)
    factor = builtins.max(0.05, 1.0 - norm * strength)
    result = target * factor
    if floor is not None:
        result = builtins.max(floor, result)
    return result

@influence_fn
def mirror(source, target, factor=1.0, **kwargs):
    """Overwrite target with source × factor (old target value ignored).
    Use as the first step when building a computed field from a param."""
    return source * factor

@influence_fn
def multiply(source, target, **kwargs):
    """Multiply target by source. Useful for chaining computed field steps."""
    return target * source

@influence_fn
def divide(source, target, **kwargs):
    """Divide target by source (safe: returns 0 when source == 0)."""
    return target / source if source != 0 else 0.0


@influence_fn
def degradation_factor(source, target, lifetime: int = 25, **kwargs):
    """Scale target by the average retained efficiency over system lifetime.

    source   = annual degradation rate (%, e.g. 0.5 for 0.5%/yr)
    lifetime = system lifetime in years (default 25)

    Uses the geometric-series average yield factor:
        avg = (1 − (1−r)^N) / (N·r),  r = source/100

    At 0.5%/yr for 25 yrs → avg ≈ 0.882 (panels retain 88.2% average yield).
    """
    if source <= 0:
        return target
    r = source / 100.0
    avg = (1.0 - (1.0 - r) ** lifetime) / (lifetime * r)
    return target * avg


# ── 3. Data Structures ─────────────────────────────────────────────────────────
@dataclass
class Range:
    """Typed min/max pair. Passed to presets instead of string-keyed override dicts."""
    min: float
    max: float

@dataclass
class ParamSpec:
    name:        str
    dist:        Callable[..., list[Any]]
    min:         float | None = None
    max:         float | None = None
    values:      list  | None = None
    dist_kwargs: dict         = field(default_factory=dict)

@dataclass
class InfluenceRule:
    source: str
    target: str
    fn:     Callable[..., Any]
    kwargs: dict = field(default_factory=dict)

@dataclass
class DefaultConstraint:
    """A solver constraint bundled with a template as a sensible starting point.

    kind: 'sum_le' | 'sum_ge' | 'sum_eq'
    The frontend/API layer uses these to pre-populate the constraint builder.
    """
    name:       str
    kind:       str
    param_name: str
    bound:      float

@dataclass
class Template:
    """A named bundle of params + influences + optional filter — the unit of reuse.

    Templates decouple domain knowledge from the generator engine.
    Each use case (product sourcing, solar panels, production lines) provides
    its own template instead of hard-coding params in gen.py.
    """
    name:             str
    params:           list[ParamSpec]           = field(default_factory=list)
    influences:       list[InfluenceRule]       = field(default_factory=list)
    filter_fn:        Callable | None           = None
    constants:        dict                      = field(default_factory=dict)
    # Non-distributed scalars (e.g. demand_modifier) go in constants — they are
    # merged into every row without becoming a Cartesian axis.
    constraints:      list[DefaultConstraint]   = field(default_factory=list)
    objective_param:  str                       = "demand"
    objective_sense:  str                       = "maximize"

# ── 4. Core Pipeline Functions ─────────────────────────────────────────────────
# resolve_dist / resolve_infl: used at API boundary and inside segmented().
def resolve_dist(dist):
    return DIST_REGISTRY[dist] if isinstance(dist, str) else dist

def resolve_infl(fn):
    return INFL_REGISTRY[fn] if isinstance(fn, str) else fn

def param_count(spec: ParamSpec) -> int:
    """Fast axis size — no generation unless needed.
    Uses count_fn if the distribution registered one, otherwise generates and measures.
    """
    if spec.values is not None:
        return len(spec.values)
    if spec.min is None or spec.max is None:
        return 1
    count_fn = COUNT_REGISTRY.get(spec.dist.__name__)
    if count_fn is not None:
        return count_fn(spec.min, spec.max, **spec.dist_kwargs)
    return len(generate_axis(spec))

def generate_axis(spec: ParamSpec) -> list:
    if spec.values is not None:
        return spec.values
    if spec.min is None or spec.max is None:
        return [None]
    return spec.dist(spec.min, spec.max, **spec.dist_kwargs)

def apply_influence(rule: InfluenceRule, source_val, target_val):
    return rule.fn(source_val, target_val, **rule.kwargs)

def apply_influences(row: dict, influences: list) -> dict:
    for rule in influences:
        src = row.get(rule.source)
        tgt = row.get(rule.target)
        if src is not None and tgt is not None:
            row[rule.target] = apply_influence(rule, src, tgt)
    return row


# ── 5. ID Builder ──────────────────────────────────────────────────────────────
def idbuilder(template_name: str | None, *param_specs: ParamSpec) -> str:
    """Structured ID prefix from template name + param ranges.
    e.g. "product_PRI1-10000_DEM1-500" or "solar_panel_EFF15-23_COS0.2-0.8"
    """
    parts = []
    if template_name:
        parts.append(template_name)
    for spec in param_specs:
        tag = spec.name[:3].upper()
        lo = spec.min if spec.min is not None else "x"
        hi = spec.max if spec.max is not None else "x"
        parts.append(f"{tag}{lo}-{hi}")
    return "_".join(parts)


# ── 6. Cartesian Generator ─────────────────────────────────────────────────────
def _to_native(v):
    """Convert numpy scalars to plain Python ints/floats for JSON serialisation."""
    if isinstance(v, np.integer): return int(v)
    if isinstance(v, np.floating): return float(v)
    return v

def cartesian_generator(
    *param_specs: ParamSpec,
    influences:    list[InfluenceRule] = (),
    filter_fn:     Callable | None     = None,
    template_name: str | None          = None,
    constants:     dict | None         = None,
) -> list[dict]:
    id_prefix   = idbuilder(template_name, *param_specs)
    param_names = [spec.name for spec in param_specs]
    generated   = []
    _constants  = constants or {}

    for idx, combo in enumerate(itertools.product(*[generate_axis(spec) for spec in param_specs]), start=1):
        row = {k: _to_native(v) for k, v in zip(param_names, combo)}
        row.update(_constants)
        row = apply_influences(row, influences)
        row = {k: _to_native(v) for k, v in row.items()}
        if filter_fn and not filter_fn(row):
            continue
        row[ID] = f"{id_prefix}{idx:06d}"
        generated.append(row)

    return generated

def from_template(template: Template) -> list[dict]:
    """Generate from a Template — the intended high-level entry point."""
    return cartesian_generator(
        *template.params,
        influences=template.influences,
        filter_fn=template.filter_fn,
        template_name=template.name,
        constants=template.constants,
    )


# ── 7. Factories ───────────────────────────────────────────────────────────────
def param(name, dist=uniform, min=None, max=None, values=None, dist_kwargs=None, **extra):
    """Build a ParamSpec. dist is resolved to a callable immediately."""
    if dist_kwargs is None:
        dist_kwargs = extra
    return ParamSpec(name=name, dist=resolve_dist(dist), min=min, max=max, values=values, dist_kwargs=dist_kwargs)

def influence(source, target, fn, **kwargs):
    """Build an InfluenceRule. source/target become param name strings; fn is resolved."""
    src = source.name if isinstance(source, ParamSpec) else source
    tgt = target.name if isinstance(target, ParamSpec) else target
    return InfluenceRule(source=src, target=tgt, fn=resolve_infl(fn), kwargs=kwargs)


# ── 8. Shared Param Names ────────────────────────────────────────────────────
# Single source of truth for field name strings.
# Templates, presets, and influence rules all reference these constants.

# generic product
PRICE            = "price"
WEIGHT           = "weight"
VOLUME           = "volume"
MARKUP           = "markup"
DEMAND           = "demand"

# solar panel — Cartesian axes
EFFICIENCY       = "efficiency"
COST_PER_WATT    = "cost_per_watt"
DEGRADATION_RATE = "degradation_rate"   # %/year panel efficiency loss
BATTERY_KWH      = "battery_kwh"        # storage capacity: 0, 5, 10, 15, 20 kWh
LOAN_TERM_YEARS  = "loan_term_years"    # financing: 0 (cash), 10, 20, 25 yr
INTEREST_RATE_PCT = "interest_rate_pct" # annual % interest on loan

# solar panel — constants and computed fields
SUNLIGHT_HOURS   = "sunlight_hours"     # annual avg PSH (constant per location)
PANEL_AREA_M2    = "panel_area_m2"      # m² per panel (constant)
PANEL_COST       = "panel_cost"         # $ per panel: panel_kwp × cost_per_watt
SYSTEM_COST      = "system_cost"        # upfront: panel_cost_total + battery_cost
MONTHLY_PAYMENT  = "monthly_payment"    # 0 for cash purchase
NET_VALUE        = "net_value"          # lifetime_savings − total_cost_paid (objective)
PANEL_COUNT      = "panel_count"        # sentinel = 1; forces single-item selection
ROI              = "roi"               # lifetime_savings / total_cost_paid

# production line
LABOUR_HOURS     = "labour_hours"
MACHINE_CAPACITY = "machine_capacity"
MATERIAL_COST    = "material_cost"
THROUGHPUT       = "throughput"


# ── 9. Template Configs ───────────────────────────────────────────────────────
# Typed override structs — one per template.
# Attribute names correspond to the param name constants above.
# Constructed at the wire boundary (main.py), consumed by presets.
@dataclass
class GenericProductConfig:
    price:  Range = field(default_factory=lambda: Range(1,    10_000))  
    weight: Range = field(default_factory=lambda: Range(0.01, 50))
    volume: Range = field(default_factory=lambda: Range(0.001, 1))
    demand: Range = field(default_factory=lambda: Range(1,    500))

@dataclass
class SolarPanelConfig:
    # Cartesian axes (generate all combinations of panel quality)
    efficiency:           Range      = field(default_factory=lambda: Range(15,   23))
    cost_per_watt:        Range      = field(default_factory=lambda: Range(0.20, 0.80))
    degradation_rate:     Range      = field(default_factory=lambda: Range(0.3,  0.8))
    # Battery/financing axes are fixed discrete lists — see battery_kwh_preset etc.
    # Single-value constants (merged into every row)
    panel_area_m2:        float      = 1.7    # m² per standard residential panel
    sunlight_hours_value: float      = 4.5    # annual avg PSH (from location or default)
    electricity_rate:     float      = 0.28   # $/kWh — user's current grid tariff
    feed_in_rate:         float      = 0.08   # $/kWh — sell-back rate to grid
    system_lifetime_years: int       = 25
    # System sizing (set by API; computed from roof_area_m2 / panel_area_m2)
    n_panels:             int        = 17     # number of panels installed
    daily_kwh:            float      = 10.0   # household daily consumption (for self-ratio)
    battery_cost_per_kwh: float      = 800.0  # $/kWh for battery storage hardware
    # Location inputs: when set, sunlight_hours_value is derived from the solar model.
    lat:                  float|None = None
    tilt:                 float|None = None
    azimuth:              float|None = None

@dataclass
class ProductionLineConfig:
    labour_hours:     Range = field(default_factory=lambda: Range(1,   24))
    machine_capacity: Range = field(default_factory=lambda: Range(100, 10000))
    material_cost:    Range = field(default_factory=lambda: Range(0.5, 50))
    throughput:       Range = field(default_factory=lambda: Range(10,  1000))
    # TODO: defect_rate: Range


# ── 10. Param Presets ─────────────────────────────────────────────────────────
# Reusable param builders. Each takes an optional Range (typed min/max).
# The default Range matches the corresponding template config default.
def demand_preset(range: Range | None = None, dist=power, **kw):
    r = range or Range(1, 500)
    return param(DEMAND, dist=dist, min=r.min, max=r.max, **kw)


# ── 11. Filter Builders ───────────────────────────────────────────────────────
# Returns a filter_fn suitable for Template.filter_fn or cartesian_generator.
def logifier_score(
    *,
    density_floor: float = 50.0,
    density_ceiling: float = 20_000.0,
    price_per_litre_ceiling: float = 5_000_000.0,
    price_size_threshold: float = 0.0005,
) -> Callable[[dict], float]:
    """Return a scoring function: 1.0 = fully plausible, 0.0 = impossible.

    Items within the physical plausibility band score 1.0.
    Items outside the band score proportionally lower — the further outside,
    the closer to 0. Used by :func:`logifier` for probabilistic sampling and
    by the count endpoint for expected-count estimation.

    Rules:

    1. **Density** — ``weight / volume`` outside [floor, ceiling] kg/m³.
       Score ramps linearly: at the boundary = 1.0, toward 0 as density
       diverges (``density/floor`` below floor; ``ceiling/density`` above).

    2. **Price-size** — tiny items (volume < threshold m³) with extreme $/m³.
       Score ramps from 1.0 at the ceiling down toward 0.
    """
    def _score(row: dict) -> float:
        prob = 1.0
        w = row.get(WEIGHT)
        v = row.get(VOLUME)
        p = row.get(PRICE)

        if w is not None and v is not None and v > 0:
            density = w / v
            if density < density_floor:
                prob *= density / density_floor          # ramp to 0 as density → 0
            elif density > density_ceiling:
                prob *= density_ceiling / density        # ramp to 0 as density → ∞

        if p is not None and v is not None and v > 0 and v < price_size_threshold:
            ppL = p / v
            if ppL > price_per_litre_ceiling:
                prob *= price_per_litre_ceiling / ppL    # ramp to 0 as price/L → ∞

        return prob

    return _score

def logifier(
    *,
    density_floor: float = 50.0,
    density_ceiling: float = 20_000.0,
    price_per_litre_ceiling: float = 5_000_000.0,
    price_size_threshold: float = 0.0005,
) -> Callable[[dict], bool]:
    """Probabilistic plausibility filter built on :func:`logifier_score`.

    Items scoring 1.0 always pass. Items scoring < 1.0 pass with that
    probability — so implausible items appear *less* rather than never.
    The further outside the plausibility band, the fewer generated.

    Use ``logifier_score(...)`` directly if you need the raw probability
    (e.g. for expected-count estimation without randomness).
    """
    score = logifier_score(
        density_floor=density_floor,
        density_ceiling=density_ceiling,
        price_per_litre_ceiling=price_per_litre_ceiling,
        price_size_threshold=price_size_threshold,
    )

    def _filter(row: dict) -> bool:
        return random.random() < score(row)

    return _filter
    
def price_preset(range: Range | None = None, dist=power, **kw):
    r = range or Range(1, 10_000)
    return param(PRICE, dist=dist, min=r.min, max=r.max, **kw)

def weight_preset(range: Range | None = None, dist=gaussian, **kw):
    r = range or Range(0.01, 50) # 10g - 50kg
    return param(WEIGHT, dist=dist, min=r.min, max=r.max, **kw)

def volume_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(0.001, 1)  # 0.001 m³ (1 L) – 1 m³ (1000 L)
    return param(VOLUME, dist=dist, min=r.min, max=r.max, **kw)

def markup_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(1.0, 3.0)
    return param(MARKUP, dist=dist, min=r.min, max=r.max, **kw)

def efficiency_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(15, 23)
    return param(EFFICIENCY, dist=dist, min=r.min, max=r.max, **kw)

def cost_per_watt_preset(range: Range | None = None, dist=power, **kw):
    r = range or Range(0.20, 0.80)
    return param(COST_PER_WATT, dist=dist, min=r.min, max=r.max, **kw)

def sunlight_hours_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(3, 8)
    return param(SUNLIGHT_HOURS, dist=dist, min=r.min, max=r.max, **kw)

def degradation_rate_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(0.3, 0.8)  # %/yr; commercial range 0.3–0.7%/yr
    return param(DEGRADATION_RATE, dist=dist, min=r.min, max=r.max, **kw)

def battery_kwh_preset():
    """Discrete battery capacity options: 0 (no battery), 5, 10, 15, 20 kWh."""
    return param(BATTERY_KWH, values=[0.0, 5.0, 10.0, 15.0, 20.0])

def loan_term_preset():
    """Standard loan terms: 0 = cash purchase, then 10, 20, 25 year loans."""
    return param(LOAN_TERM_YEARS, values=[0.0, 10.0, 20.0, 25.0])

def interest_rate_preset():
    """Typical annual interest rates: 3%, 5%, 7%."""
    return param(INTEREST_RATE_PCT, values=[3.0, 5.0, 7.0])

def labour_hours_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(1, 24)
    return param(LABOUR_HOURS, dist=dist, min=r.min, max=r.max, **kw)

def machine_capacity_preset(range: Range | None = None, dist=step, **kw):
    r = range or Range(100, 10000)
    return param(MACHINE_CAPACITY, dist=dist, min=r.min, max=r.max, **kw)

def material_cost_preset(range: Range | None = None, dist=power, **kw):
    r = range or Range(0.5, 50)
    return param(MATERIAL_COST, dist=dist, min=r.min, max=r.max, **kw)

def throughput_preset(range: Range | None = None, dist=uniform, **kw):
    r = range or Range(10, 1000)
    return param(THROUGHPUT, dist=dist, min=r.min, max=r.max, **kw)


# ── 12. Influence Presets ─────────────────────────────────────────────────────
# Reusable influence recipes for common param relationships.
# Each returns an InfluenceRule. Templates pick from these.
def price_scales_demand(price_spec, demand_spec, strength=0.8):
    """Higher price → lower demand (normalized inverse).

    At min price demand is unchanged; at max price demand is reduced to (1-strength)×original.
    Result is floored at demand_spec.min so values never go negative.
    """
    return influence(
        price_spec, demand_spec, fn=normalized_inverse,
        source_min=float(price_spec.min or 0),
        source_max=float(price_spec.max or 1),
        strength=strength,
        floor=float(demand_spec.min or 1),
    )

def markup_scales_price(markup_spec, price_spec, factor=1.0):
    """Markup multiplier applied to price."""
    return influence(markup_spec, price_spec, fn=scale, factor=factor)

def price_offsets_demand(price_spec, demand_spec, factor=-0.5):
    """Price adds a linear offset to demand (alternative to scaling)."""
    return influence(price_spec, demand_spec, fn=offset, factor=factor)

def efficiency_scale(eff_spec, cost_spec, factor=0.02):
    """Higher efficiency → higher cost per unit."""
    return influence(eff_spec, cost_spec, fn=scale, factor=factor)

def labour_scale(labour_spec, tp_spec, factor=0.1):
    """More labour hours → higher throughput, but with diminishing returns."""
    return influence(labour_spec, tp_spec, fn=scale, factor=factor)

def machine_offset(machine_spec, tp_spec, factor=0.05):
    """Higher machine capacity → linear throughput boost."""
    return influence(machine_spec, tp_spec, fn=offset, factor=factor)


# ── 13. Template Registry ─────────────────────────────────────────────────────
# Templates self-register via @template decorator — same pattern as distributions.
def template(fn):
    """Register a template builder. Template.name is derived from fn.__name__."""
    def wrapper(cfg=None):
        t = fn(cfg)
        t.name = fn.__name__
        return t
    wrapper.__name__ = fn.__name__
    wrapper.__doc__  = fn.__doc__
    TEMPLATE_REGISTRY[fn.__name__] = wrapper
    return wrapper

def get_template(name: str, cfg=None) -> Template:
    if name not in TEMPLATE_REGISTRY:
        raise KeyError(f"unknown template: {name!r}  (available: {list(TEMPLATE_REGISTRY)})")
    return TEMPLATE_REGISTRY[name](cfg)

def list_templates() -> list[str]:
    return list(TEMPLATE_REGISTRY.keys())


# ── 14. Built-in Templates ────────────────────────────────────────────────────
# Domain-specific bundles. Each @template function takes a typed config.
# Decoupled from the engine — add/remove without touching core code.

# ── generic product template ────────────────────────────────────────────────
@template
def generic_product(cfg: GenericProductConfig | None = None):
    """Generic product sourcing — the current architecture's default use case."""
    cfg = cfg or GenericProductConfig()
    # Segmented price: dense coverage at low prices, sparser as price rises.
    #   $1–$100   every $5   → 20 values  (cheap commodity band)
    #   $100–$1k  every $50  → 18 values  (mid-range band)
    #   $1k–$10k  power bias → 10 values  (premium/long-tail band)
    p = param(PRICE, dist=segmented, min=cfg.price.min, max=cfg.price.max, dist_kwargs={
        "segments": [
            {"min": cfg.price.min, "max": 100,  "dist": "step",  "kwargs": {"step": 5}},
            {"min": 100,           "max": 1000, "dist": "step",  "kwargs": {"step": 50}},
            {"min": 1000,          "max": cfg.price.max, "dist": "power", "kwargs": {"resolution": 10, "bias": 2.0}},
        ]
    })
    d = demand_preset(cfg.demand)
    w = weight_preset(cfg.weight)
    v = volume_preset(cfg.volume)
    return Template(
        name=None,
        params=[p, d, w, v],
        influences=[price_scales_demand(p, d)],
        constraints=[
            DefaultConstraint("budget", "sum_le", PRICE,  25_000),
            DefaultConstraint("space",  "sum_le", VOLUME, 5_000),
        ],
        objective_param=DEMAND,
        objective_sense="maximize",
    )


# ── solar panel template ────────────────────────────────────────────────
# Axes: efficiency × cost_per_watt × degradation_rate
#     × battery_kwh × loan_term_years × interest_rate_pct  (~3 750 combinations)
#
# Each item = one complete system configuration. The enricher computes
# system_cost, annual_savings, and net_value = lifetime_savings − total_cost_paid.
# The solver's select_one constraint (panel_count ≤ 1) forces a single winner.
# See README for the full financial model with LaTeX equations.

@template
def solar_panel(cfg: SolarPanelConfig | None = None):
    """Solar panel system — maximise net lifetime value across panel, battery, and loan options."""
    cfg = cfg or SolarPanelConfig()

    sunlight_hours = cfg.sunlight_hours_value
    if cfg.lat is not None:
        from python.solar import annual_avg_psh
        sunlight_hours = annual_avg_psh(cfg.lat, cfg.tilt, cfg.azimuth)

    # Panel quality axes (stepped for manageable Cartesian size)
    eff  = efficiency_preset(cfg.efficiency,       dist=step, dist_kwargs={"step": 2})
    cpw  = cost_per_watt_preset(cfg.cost_per_watt, dist=step, dist_kwargs={"step": 0.15})
    deg  = degradation_rate_preset(cfg.degradation_rate, dist=step, dist_kwargs={"step": 0.25})
    # Battery and financing axes (discrete)
    bat  = battery_kwh_preset()
    loan = loan_term_preset()
    rate = interest_rate_preset()

    panel_area    = cfg.panel_area_m2
    elec_rate     = cfg.electricity_rate
    feed_in       = cfg.feed_in_rate
    bat_cpkwh     = cfg.battery_cost_per_kwh
    lifetime      = cfg.system_lifetime_years
    n_panels      = cfg.n_panels
    daily_kwh_use = cfg.daily_kwh

    def enricher(row: dict) -> bool:
        eff_frac   = row.get(EFFICIENCY, 0) / 100.0
        cpw_val    = row.get(COST_PER_WATT, 0)
        deg_val    = row.get(DEGRADATION_RATE, 0)
        bat_kwh    = row.get(BATTERY_KWH, 0)
        loan_years = int(row.get(LOAN_TERM_YEARS, 0))
        rate_pct   = row.get(INTEREST_RATE_PCT, 5.0)

        # Cash purchases give identical results regardless of interest rate;
        # keep only one rate value to avoid duplicates in the solver catalog.
        if loan_years == 0 and rate_pct != 3.0:
            return False

        # ── System cost ───────────────────────────────────────────────────────
        panel_kwp        = eff_frac * panel_area * 1000.0       # W peak per panel
        panel_cost_total = panel_kwp * cpw_val * n_panels        # $ all panels
        battery_cost     = bat_kwh * bat_cpkwh                   # $
        system_cost      = panel_cost_total + battery_cost       # $ upfront
        if system_cost <= 0:
            return False

        # ── Energy generation and savings ─────────────────────────────────────
        daily_kwh_gen  = eff_frac * sunlight_hours * panel_area * n_panels

        base_self      = 0.30
        battery_boost  = min(0.55, bat_kwh / max(1.0, daily_kwh_use))
        self_ratio     = min(0.85, base_self + battery_boost)

        if deg_val > 0:
            r          = deg_val / 100.0
            avg_factor = (1.0 - (1.0 - r) ** lifetime) / (lifetime * r)
        else:
            avg_factor = 1.0

        annual_savings   = (daily_kwh_gen * self_ratio * elec_rate
                          + daily_kwh_gen * (1.0 - self_ratio) * feed_in) * 365.0
        lifetime_savings = annual_savings * lifetime * avg_factor

        # ── Financing ─────────────────────────────────────────────────────────
        if loan_years > 0:
            r_m      = rate_pct / 100.0 / 12.0
            n_months = loan_years * 12
            if r_m > 0:
                monthly_pmt = (system_cost * r_m * (1.0 + r_m) ** n_months
                               / ((1.0 + r_m) ** n_months - 1.0))
            else:
                monthly_pmt = system_cost / n_months
            total_paid = monthly_pmt * n_months
        else:
            monthly_pmt = 0.0
            total_paid  = system_cost

        net_value = lifetime_savings - total_paid
        roi       = lifetime_savings / total_paid if total_paid > 0 else 0.0

        row[SYSTEM_COST]        = round(system_cost, 2)
        row[MONTHLY_PAYMENT]    = round(monthly_pmt, 2)
        row[NET_VALUE]          = round(net_value, 2)
        row[PANEL_COUNT]        = 1          # sentinel: forces solver to pick at most 1 system
        row[ROI]                = round(roi, 4)
        row['annual_savings']   = round(annual_savings, 2)
        row['lifetime_savings'] = round(lifetime_savings, 2)
        row['self_ratio']       = round(self_ratio, 3)
        row['panel_cost_total'] = round(panel_cost_total, 2)
        row['battery_cost']     = round(battery_cost, 2)

        return net_value > 0.0

    return Template(
        name=None,
        params=[eff, cpw, deg, bat, loan, rate],
        constants={
            PANEL_AREA_M2:  panel_area,
            SUNLIGHT_HOURS: round(sunlight_hours, 2),
        },
        filter_fn=enricher,
        constraints=[
            DefaultConstraint("budget",     "sum_le", SYSTEM_COST,    10_000.0),
            DefaultConstraint("select_one", "sum_le", PANEL_COUNT,     1.0),
        ],
        objective_param=NET_VALUE,
        objective_sense="maximize",
    )


# ── production line template ────────────────────────────────────────────
# Axes: labour_hours × machine_capacity × material_cost × throughput
# Objective: maximise throughput subject to labour and material budgets.
# Status: stub — constraints not yet wired to solver; defect_rate planned.
@template
def production_line(cfg: ProductionLineConfig | None = None):
    """Production line optimisation — labour, machine, and material constraints."""
    cfg = cfg or ProductionLineConfig()
    lab = labour_hours_preset(cfg.labour_hours)
    mac = machine_capacity_preset(cfg.machine_capacity, step=100)
    mat = material_cost_preset(cfg.material_cost, bias=1.3)
    tp  = throughput_preset(cfg.throughput)

    return Template(
        name=None,
        params=[lab, mac, mat, tp],
        influences=[
            labour_scale(lab, tp),
            machine_offset(mac, tp),
            efficiency_scale(mat, tp),
        ],
        constraints=[
            DefaultConstraint("labour",    "sum_le", LABOUR_HOURS,  40.0),
            DefaultConstraint("materials", "sum_le", MATERIAL_COST, 100.0),
        ],
        objective_param=THROUGHPUT,
        objective_sense="maximize",
    )
