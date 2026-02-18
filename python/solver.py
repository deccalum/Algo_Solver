"""
procurement engine
Multi-Period Inventory Purchase Optimization using Integer Programming
Solver: Google OR-Tools SCIP
"""

import os
import time
import glob
from typing import List, Dict, Optional, Any
from ortools.linear_solver import pywraplp
import traceback

from common import Product, Transits, dataclass, ProductRepository

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class SolverConfig:
    """Configuration for the optimization constraints"""
    budget_constraint: Optional[float] = None
    space_constraint: Optional[float] = None
    
@dataclass
class TransitCost:
    """Handles transit cost calculations based on product transit modes"""
    
    @staticmethod
    def get_transit(mode: Transits) -> tuple[float, float]:
        """Returns (capacity, cost_per_unit) for the given transit mode"""
        if mode == Transits.COURIER:
            return 50.0, 20.0
        elif mode == Transits.CONTAINER:
            return 50000.0, 1500.0
        elif mode == Transits.PALLET:
            return 5000.0, 400.0
        
    def calculate_cost(self, solver: pywraplp.Solver, products: List[Product], quantity_vars: Dict[str, Any]) -> Any:
        """
        Calculate total transit costs across all modes.
        
        For each transit mode:
        - Sum total size needed
        - Calculate minimum number of transit units required
        - Multiply by cost per unit
        
        Returns: solver expression for total transit cost
        """
        
        mode_set = set(p.transit for p in products)
        if not mode_set:
            return 0.0
        
        modes = sorted(mode_set, key=lambda m: m.name)
        cost_terms = []
        for mode in modes:
            mode_products = [p for p in products if p.transit == mode]
            if not mode_products:
                continue
            
            capacity, cost_per_unit = self.get_transit(mode)
            total_size_expr = solver.Sum([p.size * quantity_vars[p.id] for p in mode_products])
            num_units = solver.IntVar(0, solver.infinity(), f"num_{mode}")
            solver.Add(total_size_expr <= num_units * capacity)
            cost_terms.append(num_units * cost_per_unit)
        
        return solver.Sum(cost_terms) if cost_terms else 0.0

class ProcurementOptimizer:
    """Optimizes product selection to maximize profit under constraints."""
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        self.quantity_vars: Dict[str, Any] = {}
        self.transit_calculator = TransitCost()

    def optimize(self, products: List[Product]) -> Dict:
        """
        Run optimization and return results.
        
        Returns:
            Dictionary with status, objective value, and selected products
        """
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return {'status': 'ERROR', 'message': 'Failed to create SCIP solver'}
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads = 0")
        solver.SetSolverSpecificParametersAsString("presolving/maxrounds = -1")

        try:
            self._create_decision_variables(solver, products)
            self._define_objective(solver, products)
            self._add_constraints(solver, products)
            status_code = solver.Solve()
            return self._extract_solution(solver, products, status_code)
        
        except Exception as e:
            traceback.print_exc()
            return {'status': 'ERROR', 'message': str(e)}

    def _create_decision_variables(self, solver: pywraplp.Solver, products: List[Product]):
        """
        Create integer decision variables for product quantities.
        
        Each variable represents how many units of a product to purchase.
        Range: [0, stock_available]
        """
        self.quantity_vars = {}
        for product in products:
            max_qty = product.stock if self.config else 1
            self.quantity_vars[product.id] = solver.IntVar(
                0, 
                max_qty, 
                f"qty_{product.id}"
            )

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
        transit_costs = self.transit_calculator.calculate_cost(solver, products, self.quantity_vars)
        solver.Maximize(total_revenue - transit_costs)

    def _add_constraints(self, solver: pywraplp.Solver, products: List[Product]):
        """
        Add business constraints to the optimization.
        
        - Budget constraint: total spend <= available budget
        - Space constraint: total size <= available space
        """
        if self.config.budget_constraint is not None:
            total_cost = solver.Sum([
                p.price * self.quantity_vars[p.id] 
                for p in products
            ])
            solver.Add(total_cost <= self.config.budget_constraint, "budget")

        if self.config.space_constraint is not None:
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
        
        result = {'status': status,'objective_value': 0.0,'product_totals': {}}
    
        if status in ['OPTIMAL', 'FEASIBLE']:
            result['objective_value'] = solver.Objective().Value()
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
                    
        return result


if __name__ == "__main__":
    print("Loading latest generated products...")
    try:
        products = ProductRepository.load_products()
    except FileNotFoundError as e:
        print(f"{e}")
        exit(1)
    print(f"Loaded {len(products)} products")
    
    config = SolverConfig()
    optimizer = ProcurementOptimizer(config)
    print("Running optimization...")
    results = optimizer.optimize(products)
    print(f"Status: {results['status']}")
    print(f"Objective: {results.get('objective_value', 0.0):.2f}")
    print(f"Selected: {len(results.get('product_totals', {}))} products")
    output_dir = ProductRepository.get_output_dir()
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    timestamp = time.strftime("%H-%M_%d-%m")
    output_path = os.path.join(output_dir, f"{script_name}_{timestamp}.csv")
    
    ProductRepository.export_results(results, output_path)