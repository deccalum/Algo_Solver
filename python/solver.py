"""
procurement engine
Multi-Period Inventory Purchase Optimization using Integer Programming
Solver: Google OR-Tools SCIP
"""

import os
import time
from typing import List, Dict, Optional, Any
from ortools.linear_solver import pywraplp
import traceback

from common import Product, SolverConfig, Transits, ProductRepository, log, format_price, format_number, format_volume

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ProcurementOptimizer:
    """Optimizes product selection to maximize profit under constraints."""
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        self.quantity_vars: Dict[str, Any] = {}

    @staticmethod
    def _log(message: str):
        log("solver", message)

    def _calculate_transit_cost(self, solver: pywraplp.Solver, products: List[Product]) -> Any:
        """
        Calculate total transit costs grouped by transit mode using product metadata.

        Uses linearized per-size transit cost to avoid introducing additional constraints.
        """
        grouped: Dict[Transits, List[Product]] = {}
        for product in products:
            grouped.setdefault(product.transit, []).append(product)

        mode_counts = {mode.name: len(items) for mode, items in grouped.items()}
        self._log(f"Transit groups: {mode_counts}")

        cost_terms = []
        for mode, mode_products in grouped.items():
            if not mode_products:
                continue

            capacity = mode_products[0].transit_size
            cost_per_unit = mode_products[0].transit_cost
            cost_per_size = cost_per_unit / capacity
            self._log(
                f"Transit mode {mode.name}: capacity={capacity}, cost_per_unit={cost_per_unit}, "
                f"cost_per_size={cost_per_size:.6f}, "
                f"products={len(mode_products)}"
            )
            total_size_expr = solver.Sum([p.size * self.quantity_vars[p.id] for p in mode_products])
            cost_terms.append(total_size_expr * cost_per_size)

        return solver.Sum(cost_terms) if cost_terms else 0.0

    def optimize(self, products: List[Product]) -> Dict:
        """
        Run optimization and return results.
        
        Returns:
            Dictionary with status, objective value, and selected products
        """
        self._log("Optimization pipeline started")
        self._log(f"Input products: {len(products)}")

        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return {'status': 'ERROR', 'message': 'Failed to create SCIP solver'}
        solver.EnableOutput()
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads = 0")
        solver.SetSolverSpecificParametersAsString("presolving/maxrounds = -1")
        self._log("SCIP solver created and configured")

        try:
            t0 = time.time()
            self._log("Step 1/4: creating decision variables")
            self._create_decision_variables(solver, products)
            self._log(f"Decision variables created: {len(self.quantity_vars)}")

            self._log("Step 2/4: defining objective")
            self._define_objective(solver, products)

            self._log("Step 3/4: adding constraints")
            self._add_constraints(solver, products)

            self._log(
                f"Model stats before solve: num_variables={solver.NumVariables()}, "
                f"num_constraints={solver.NumConstraints()}"
            )

            self._log("Step 4/4: solving model")
            solve_start = time.time()
            status_code = solver.Solve()
            solve_duration = time.time() - solve_start
            self._log(f"Solve finished in {solve_duration:.4f}s with status_code={status_code}")

            total_duration = time.time() - t0
            self._log(f"Optimization pipeline completed in {total_duration:.4f}s")
            return self._extract_solution(solver, products, status_code)
        
        except Exception as e:
            self._log(f"Optimization failed with exception: {e}")
            traceback.print_exc()
            return {'status': 'ERROR', 'message': str(e)}

    def _create_decision_variables(self, solver: pywraplp.Solver, products: List[Product]):
        """
        Create integer decision variables for product quantities.
        
        Each variable represents how many units of a product to purchase.
        Range: [0, stock_available]
        """
        self.quantity_vars = {}
        infinite_stock_count = 0
        for product in products:
            max_qty = product.stock if self.config else 1
            if max_qty >= 2_147_483_647:
                infinite_stock_count += 1
            self.quantity_vars[product.id] = solver.IntVar(0, max_qty, f"qty_{product.id}")
        self._log(f"Variable bounds prepared. Infinite-stock products={infinite_stock_count}")

    def _define_objective(self, solver: pywraplp.Solver, products: List[Product]):
        """
        Define objective function: Maximize (revenue - transit_costs).
        
        Revenue per product = demand × (1 - logistics) × markup × price × quantity
        Transit costs calculated separately per mode
        """
        revenue_terms = []
        for p in products:
            quantity = self.quantity_vars[p.id]
            unit_revenue = p.demand * (1.0 - p.logistics) * p.markup * p.price
            revenue_terms.append(unit_revenue * quantity)
        
        total_revenue = solver.Sum(revenue_terms)
        transit_costs = self._calculate_transit_cost(solver, products)
        solver.Maximize(total_revenue - transit_costs)
        self._log(f"Objective defined with {len(revenue_terms)} revenue terms")

    def _add_constraints(self, solver: pywraplp.Solver, products: List[Product]):
        """Add business constraints to the optimization."""
        if self.config.budget_constraint is not None:
            self._log(f"Adding budget constraint: <= {format_price(self.config.budget_constraint)}")
            total_cost = solver.Sum([
                p.price * self.quantity_vars[p.id]
                for p in products
            ])
            solver.Add(total_cost <= self.config.budget_constraint)

        if self.config.space_constraint is not None:
            self._log(f"Adding space constraint: <= {format_volume(self.config.space_constraint)}")
            total_size = solver.Sum([
                p.size * self.quantity_vars[p.id] 
                for p in products
            ])
            solver.Add(total_size <= self.config.space_constraint)

    def _extract_solution(self, solver: pywraplp.Solver, products: List[Product], status_code: int) -> Dict:
        """
        Extract and format optimization results.
        
        Returns dictionary with:
        - status: solution status (OPTIMAL, FEASIBLE, etc.)
        - objective_value: final objective function value
        - product_totals: selected products with quantities and metrics
        """
        status_names = {
            pywraplp.Solver.OPTIMAL: 'OPTIMAL',
            pywraplp.Solver.FEASIBLE: 'FEASIBLE',
            pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
            pywraplp.Solver.UNBOUNDED: 'UNBOUNDED',
            pywraplp.Solver.ABNORMAL: 'ABNORMAL'
        }
        status = status_names.get(status_code, 'UNKNOWN')
        self._log(f"Extracting solution for status={status}")
        result = {'status': status,'objective_value': 0.0,'product_totals': {}}
        if status in ['OPTIMAL', 'FEASIBLE']:
            result['objective_value'] = solver.Objective().Value()
            self._log(f"Objective value: {format_price(result['objective_value'])}")
            for p in products:
                quantity = int(self.quantity_vars[p.id].solution_value())
                if quantity > 0:
                    unit_score = p.demand * (1.0 - p.logistics) * p.markup * p.price
                    result['product_totals'][p.id] = {
                        'quantity': quantity,
                        'price': p.price,
                        'size': p.size,
                        'demand': p.demand,
                        'logistics': p.logistics,
                        'markup': p.markup,
                        'stock': p.stock,
                        'transit': p.transit.name,
                        'unit_score': round(unit_score, 4),
                        'total_score': round(unit_score * quantity, 4)
                    }
            self._log(f"Selected products count: {len(result['product_totals'])}")
        else:
            self._log("No feasible/optimal solution payload to extract")
        return result

if __name__ == "__main__":
    log("solver", "Loading latest generated products...")
    products = ProductRepository.load_products()
    log("solver", f"Loaded {len(products)} products")
    config = SolverConfig()
    optimizer = ProcurementOptimizer(config)
    log("solver", "Running optimization...")
    results = optimizer.optimize(products)
    log("solver", f"Status: {results['status']}")
    objective_value = results['objective_value'] if 'objective_value' in results else 0.0
    selected_count = len(results['product_totals']) if 'product_totals' in results else 0
    log("solver", f"Objective: {objective_value:.2f}")
    log("solver", f"Selected: {selected_count} products")
    output_dir = ProductRepository.get_output_dir()
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    timestamp = time.strftime("%H-%M_%d-%m")
    output_path = os.path.join(output_dir, f"{script_name}_{timestamp}.csv")
    ProductRepository.export_results(results, output_path)