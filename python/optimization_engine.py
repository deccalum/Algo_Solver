"""
Multi-Period Inventory Purchase Optimization using Integer Programming
Solver: Google OR-Tools SCIP
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from ortools.linear_solver import pywraplp

@dataclass
class SeasonalFactors:
    """Seasonal demand multipliers by month"""
    factors: Dict[int, float] = field(default_factory=dict)

    def get(self, month: int) -> float:
        return self.factors.get(month, 1.0)

@dataclass
class DemandForecast:
    base_demand: float
    seasonal_factors: SeasonalFactors
    trend_factor: float = 1.02
    demand_buffer: float = 1.5

    def forecast_month(self, month: int) -> float:
        return self.base_demand * self.seasonal_factors.get(month) * (self.trend_factor ** (month - 1))

@dataclass
class Product:
    id: str
    wholesale_price: float
    retail_price: float
    size_cm3: float
    weight_g: float
    demand_forecast: DemandForecast
    name: str = ""
    category: str = ""
    bulk_discount_threshold: int = 0
    bulk_discount_rate: float = 0.0

    @property
    def margin(self) -> float:
        return self.retail_price - self.wholesale_price

@dataclass
class ShippingOption:
    name: str
    cost_per_kg: float
    cost_per_m3: float
    max_weight_kg: float
    max_volume_m3: float
    crosses_border: bool
    customs_duty_rate: float
    days_transit: int

@dataclass
class OptimizerConfig:
    planning_months: int
    budget_per_month: float
    warehouse_capacity_m3: float
    shipping: ShippingOption
    solver_time_limit_seconds: int = 300
    solver_type: str = 'SCIP'
    demand_multiplier: float = 1.0

class PurchaseOrderOptimizer:
    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.variables: Dict[str, Dict[int, Any]] = {}

    def optimize(self, products: List[Product]) -> Dict:
        solver = pywraplp.Solver.CreateSolver(self.config.solver_type)
        if not solver:
            return {'status': 'ERROR', 'message': f"Solver {self.config.solver_type} unavailable"}

        # Set time limit
        solver.SetTimeLimit(self.config.solver_time_limit_seconds * 1000)

        try:
            self._create_variables(solver, products)
            self._create_objective(solver, products)
            self._create_constraints(solver, products)
            
            status_code = solver.Solve()
            return self._extract_results(solver, products, status_code)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'status': 'ERROR', 'message': str(e)}

    def _create_variables(self, solver: Any, products: List[Product]):
        self.variables = {}
        for product in products:
            self.variables[product.id] = {}
            for month in range(1, self.config.planning_months + 1):
                forecast = product.demand_forecast.forecast_month(month)
                # Ensure we allow 0 but cap reasonably to reduce search space
                max_qty = int(forecast * self.config.demand_multiplier * product.demand_forecast.demand_buffer) + 10
                self.variables[product.id][month] = solver.IntVar(0, max_qty, f'q_{product.id}_m{month}')

    def _create_objective(self, solver: Any, products: List[Product]):
        objective_terms = []
        for month in range(1, self.config.planning_months + 1):
            m_vars = [self.variables[p.id][month] for p in products]
            
            # Gross Margin
            for p, v in zip(products, m_vars):
                objective_terms.append(p.margin * v)
            
            # Shipping Costs (Weight + Volume)
            total_weight_kg = sum((p.weight_g / 1000.0) * v for p, v in zip(products, m_vars))
            total_volume_m3 = sum((p.size_cm3 / 1_000_000.0) * v for p, v in zip(products, m_vars))
            
            objective_terms.append(-(self.config.shipping.cost_per_kg * total_weight_kg))
            objective_terms.append(-(self.config.shipping.cost_per_m3 * total_volume_m3))
            
            if self.config.shipping.crosses_border:
                total_wholesale = sum(p.wholesale_price * v for p, v in zip(products, m_vars))
                objective_terms.append(-(self.config.shipping.customs_duty_rate * total_wholesale))
        
        solver.Maximize(sum(objective_terms))

    def _create_constraints(self, solver: Any, products: List[Product]):
        for month in range(1, self.config.planning_months + 1):
            m_vars = [self.variables[p.id][month] for p in products]
            
            # Budget
            solver.Add(sum(p.wholesale_price * v for p, v in zip(products, m_vars)) <= self.config.budget_per_month)
            # Shipping Weight
            solver.Add(sum((p.weight_g / 1000.0) * v for p, v in zip(products, m_vars)) <= self.config.shipping.max_weight_kg)
            # Shipping Volume per month
            solver.Add(sum((p.size_cm3 / 1_000_000.0) * v for p, v in zip(products, m_vars)) <= self.config.shipping.max_volume_m3)
            # Warehouse Capacity per month
            solver.Add(sum((p.size_cm3 / 1_000_000.0) * v for p, v in zip(products, m_vars)) <= self.config.warehouse_capacity_m3)

    def _extract_results(self, solver: Any, products: List[Product], status_code: int) -> Dict:
        status_map = {
            pywraplp.Solver.OPTIMAL: 'OPTIMAL',
            pywraplp.Solver.FEASIBLE: 'FEASIBLE',
            pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
            pywraplp.Solver.UNBOUNDED: 'UNBOUNDED',
            pywraplp.Solver.ABNORMAL: 'ABNORMAL'
        }
        status = status_map.get(status_code, 'UNKNOWN')
        
        result = {
            'status': status,
            'objective_value': 0.0,
            'quantities': {},
            'product_totals': {}
        }
        
        if status in ['OPTIMAL', 'FEASIBLE']:
            result['objective_value'] = solver.Objective().Value()
            
            for p in products:
                # Quantities per month
                p_quants = {}
                total_qty = 0
                for m in range(1, self.config.planning_months + 1):
                    val = int(self.variables[p.id][m].solution_value())
                    if val > 0:
                        p_quants[m] = val
                        total_qty += val
                
                if total_qty > 0:
                    result['quantities'][p.id] = p_quants
                    
                    # Calculate totals for export
                    cost = total_qty * p.wholesale_price
                    revenue = total_qty * p.retail_price
                    margin = revenue - cost
                    
                    result['product_totals'][p.id] = {
                        'name': p.name,
                        'total_quantity': total_qty,
                        'total_cost': cost,
                        'total_revenue': revenue,
                        'total_margin': margin
                    }
                
        return result
