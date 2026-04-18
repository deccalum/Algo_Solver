# solver.py — SCIP optimisation
from dataclasses import dataclass, field
from enum import Enum
from ortools.linear_solver import pywraplp


# ── Enums ────────────────────────────────────────────────────────────────────
class ConstraintKind(str, Enum):
    SUM_LE = "sum_le"   # Σ (coeff[i] * var[i]) ≤ bound
    SUM_GE = "sum_ge"   # Σ (coeff[i] * var[i]) ≥ bound
    SUM_EQ = "sum_eq"   # Σ (coeff[i] * var[i]) = bound

class Sense(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


# ── Data Structures ──────────────────────────────────────────────────────────
@dataclass
class ConstraintSpec:
    name:       str
    kind:       ConstraintKind
    param_name: str    # which generated field supplies the per-item coefficients
    bound:      float
    # TODO: coeff_fn — per-item coefficient override instead of raw field value

@dataclass
class SolveRequest:
    """Everything the solver needs — built from generator output + template metadata."""
    items:           list[dict]
    constraints:     list[ConstraintSpec] = field(default_factory=list)
    objective_param: str                  = "demand"
    objective_sense: Sense                = Sense.MAXIMIZE
    # TODO: multi-space — list of SolveRequests sharing global constraints

@dataclass
class SolveResult:
    objective_value: float | None
    selections:      list[dict]
    # TODO: shadow_prices — dual values for constraint sensitivity analysis


# ── Solver ───────────────────────────────────────────────────────────────────
def optimize(request: SolveRequest) -> SolveResult:
    """Run SCIP on a SolveRequest and return structured results."""
    slvr  = pywraplp.Solver.CreateSolver("SCIP")
    items = request.items

    x = {item["id"]: slvr.BoolVar(item["id"]) for item in items}

    for cs in request.constraints:
        ct = slvr.Constraint(-slvr.infinity(), cs.bound, cs.name)
        if cs.kind is ConstraintKind.SUM_GE:
            ct.SetBounds(cs.bound, slvr.infinity())
        elif cs.kind is ConstraintKind.SUM_EQ:
            ct.SetBounds(cs.bound, cs.bound)
        for item in items:
            ct.SetCoefficient(x[item["id"]], item.get(cs.param_name, 0))

    obj = slvr.Objective()
    for item in items:
        obj.SetCoefficient(x[item["id"]], item.get(request.objective_param, 0))
    if request.objective_sense is Sense.MAXIMIZE:
        obj.SetMaximization()
    else:
        obj.SetMinimization()

    slvr.Solve()
    selections = [item for item in items if x[item["id"]].solution_value() > 0.5]
    return SolveResult(obj.Value(), selections)
