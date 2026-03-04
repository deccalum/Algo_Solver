"""
procurement engine
Multi-Period Inventory Purchase Optimization using Integer Programming
Solver: Google OR-Tools SCIP
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ortools.linear_solver import pywraplp

import algsolver_pb2
from common import format_price, format_volume, log


@dataclass
class SolverConfig:
    budget_constraint: Optional[float] = None
    space_constraint: Optional[float] = None


class ProcurementOptimizer:
    """Optimizes product selection to maximize profit under constraints."""

    def __init__(self, config: Optional[SolverConfig] = None):
        """Initialize optimizer with optional budget/space constraints."""
        self.config = config or SolverConfig()
        self.quantity_vars: Dict[str, Any] = {}

    @staticmethod
    def _log(message: str):
        """Write structured solver logs."""
        log("solver", message)

    def _calculate_transit_cost(
        self, solver: pywraplp.Solver, products: List[algsolver_pb2.ProductItem]
    ) -> Any:
        """Calculate total transit costs grouped by transit mode."""
        grouped: Dict[str, List[algsolver_pb2.ProductItem]] = {}
        for product in products:
            grouped.setdefault(product.transit, []).append(product)

        cost_terms = []
        for mode, mode_products in grouped.items():
            if not mode_products:
                continue

            capacity = mode_products[0].transit_size
            cost_per_unit = mode_products[0].transit_cost
            cost_per_size = cost_per_unit / capacity
            self._log(
                f"Transit mode {mode}: capacity={capacity}, cost_per_unit={cost_per_unit}, "
                f"cost_per_size={cost_per_size:.6f}, products={len(mode_products)}"
            )
            total_size_expr = solver.Sum(
                [p.size * self.quantity_vars[p.id] for p in mode_products]
            )
            cost_terms.append(total_size_expr * cost_per_size)

        return solver.Sum(cost_terms) if cost_terms else 0.0

    def optimize(self, products: List[algsolver_pb2.ProductItem]) -> Dict:
        """Run optimization and return status, objective, and selected products."""
        self._log("Optimization pipeline started")
        self._log(f"Input products: {len(products)}")

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            return {"status": "ERROR", "message": "Failed to create SCIP solver"}

        solver.EnableOutput()
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads = 0")
        solver.SetSolverSpecificParametersAsString("presolving/maxrounds = -1")

        self._create_decision_variables(solver, products)
        self._define_objective(solver, products)
        self._add_constraints(solver, products)

        status_code = solver.Solve()
        return self._extract_solution(solver, products, status_code)

    def _create_decision_variables(
        self, solver: pywraplp.Solver, products: List[algsolver_pb2.ProductItem]
    ):
        """Create integer decision variables for each product quantity."""
        self.quantity_vars = {}
        for product in products:
            max_qty = product.stock
            self.quantity_vars[product.id] = solver.IntVar(
                0, max_qty, f"qty_{product.id}"
            )

    def _define_objective(
        self, solver: pywraplp.Solver, products: List[algsolver_pb2.ProductItem]
    ):
        """Define objective function: maximize revenue minus transit cost."""
        revenue_terms = []
        for product in products:
            quantity = self.quantity_vars[product.id]
            unit_revenue = (
                product.demand
                * (1.0 - product.logistics)
                * product.markup
                * product.price
            )
            revenue_terms.append(unit_revenue * quantity)

        total_revenue = solver.Sum(revenue_terms)
        transit_costs = self._calculate_transit_cost(solver, products)
        solver.Maximize(total_revenue - transit_costs)

    def _add_constraints(
        self, solver: pywraplp.Solver, products: List[algsolver_pb2.ProductItem]
    ):
        """Add budget and space constraints when configured."""
        if self.config.budget_constraint is not None:
            self._log(
                f"Adding budget constraint: <= {format_price(self.config.budget_constraint)}"
            )
            total_cost = solver.Sum(
                [product.price * self.quantity_vars[product.id] for product in products]
            )
            solver.Add(total_cost <= self.config.budget_constraint)

        if self.config.space_constraint is not None:
            self._log(
                f"Adding space constraint: <= {format_volume(self.config.space_constraint)}"
            )
            total_size = solver.Sum(
                [product.size * self.quantity_vars[product.id] for product in products]
            )
            solver.Add(total_size <= self.config.space_constraint)

    def _extract_solution(
        self,
        solver: pywraplp.Solver,
        products: List[algsolver_pb2.ProductItem],
        status_code: int,
    ) -> Dict:
        """Extract solver output into serializable result dictionary."""
        status_names = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE",
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
            pywraplp.Solver.ABNORMAL: "ABNORMAL",
        }
        status = status_names.get(status_code, "UNKNOWN")
        result = {"status": status, "objective_value": 0.0, "product_totals": {}}

        if status in ["OPTIMAL", "FEASIBLE"]:
            result["objective_value"] = solver.Objective().Value()
            for product in products:
                quantity = int(self.quantity_vars[product.id].solution_value())
                if quantity <= 0:
                    continue

                unit_score = (
                    product.demand
                    * (1.0 - product.logistics)
                    * product.markup
                    * product.price
                )
                result["product_totals"][product.id] = {
                    "quantity": quantity,
                    "price": product.price,
                    "size": product.size,
                    "demand": product.demand,
                    "logistics": product.logistics,
                    "markup": product.markup,
                    "stock": product.stock,
                    "transit": product.transit,
                    "unit_score": round(unit_score, 4),
                    "total_score": round(unit_score * quantity, 4),
                }

        return result
