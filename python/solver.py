"""
Multi-Period Inventory Purchase Optimization using Integer Programming
Solver: Google OR-Tools SCIP
"""

import os
import time
from glob import glob
from typing import List, Dict, Optional, Any
from ortools.linear_solver import pywraplp
import traceback

from common import Product, Space, PRICE_CONSTRAINTS, SPACE_CONSTRAINTS, load_products, export_results

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Optimizer:
    def __init__(self, constraints: Optional[Space] = None):
        self.variables: Dict[str, Any] = {}
        self.constraints = constraints

    def optimize(self, products: List[Product]) -> Dict:
        solver = pywraplp.Solver.CreateSolver(solver_id='SCIP')
        
        # Performance tuning parameters
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads = 0")
        solver.SetSolverSpecificParametersAsString("presolving/maxrounds = -1")

        try:
            self.create_variables(solver, products)
            self.create_objective(solver, products)
            self.create_constraints(solver, products)
            
            status_code = solver.Solve()
            return self.extract_results(solver, products, status_code)
        
        except Exception as e:
            traceback.print_exc()
            return {'status': 'ERROR', 'message': str(e)}

    def create_variables(self, solver: Any, products: List[Product]):
        self.variables = {}
        for product in products:
            # Integer selection variable (0 to max_quantity)
            # If unconstrained (scoring), limit to 1 to produce a ranking
            if self.constraints is None:
                self.variables[product.id] = solver.IntVar(0, 1, f"select_{product.id}")
            else:
                self.variables[product.id] = solver.IntVar(0, product.max_quantity, f"select_{product.id}")

    def create_objective(self, solver: Any, products: List[Product]):
        objective_terms = []
        for p in products:
            v = self.variables[p.id]
            score = p.demand * (1.0 - p.logistics) * p.markup * p.price
            objective_terms.append(score * v)
        
        solver.Maximize(sum(objective_terms))

    def create_constraints(self, solver: Any, products: List[Product]):
        m_vars = [self.variables[p.id] for p in products]

        if self.constraints is None:
            return

        if self.constraints.price_constraint is not None:
            solver.Add(sum(p.price * v for p, v in zip(products, m_vars)) <= self.constraints.price_constraint)

        if self.constraints.space_constraint is not None:
            solver.Add(sum(p.size * v for p, v in zip(products, m_vars)) <= self.constraints.space_constraint)

    def extract_results(self, solver: Any, products: List[Product], status_code: int) -> Dict:
        status_map = {
            pywraplp.Solver.OPTIMAL: 'OPTIMAL',
            pywraplp.Solver.FEASIBLE: 'FEASIBLE',
            pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
            pywraplp.Solver.UNBOUNDED: 'UNBOUNDED',
            pywraplp.Solver.ABNORMAL: 'ABNORMAL'
        }
        status = status_map[status_code]
        
        result = {
            'status': status,
            'objective_value': 0.0,
            'product_totals': {}
        }
        
        if status in ['OPTIMAL', 'FEASIBLE']:
            result['objective_value'] = solver.Objective().Value()
            
            for p in products:
                val = int(self.variables[p.id].solution_value())
                if val > 0:
                    # Recalculate score for report
                    score = round(p.demand * (1.0 - p.logistics) * p.markup * p.price, 4)
                    result['product_totals'][p.id] = {
                        'quantity': val,
                        'price': p.price,
                        'size': p.size,
                        'demand': p.demand,
                        'logistics': p.logistics,
                        'markup': p.markup,
                        'max_quantity': p.max_quantity,
                        'score': score
                    }
                
        return result


def _latest_generated_csv(output_dir: str) -> Optional[str]:
    pattern = os.path.join(output_dir, "*_generated_*.csv")
    candidates = glob(pattern)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


if __name__ == "__main__":
    output_dir = os.path.join(PROJECT_ROOT, "data", "output")
    input_path = _latest_generated_csv(output_dir)
    if not input_path:
        raise FileNotFoundError("No generated CSV found in data/output.")

    products = load_products(input_path)
    if not products:
        raise ValueError("No products loaded from latest generated CSV.")

    constraints = Space(
        price_constraint=PRICE_CONSTRAINTS,
        space_constraint=SPACE_CONSTRAINTS
    )
    optimizer = Optimizer(constraints=constraints)
    results = optimizer.optimize(products)

    script_name = os.path.splitext(os.path.basename(__file__))[0]
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    output_path = os.path.join(output_dir, f"{script_name}_{timestamp}.csv")
    export_results(results, output_path)
