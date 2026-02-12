"""
Parameter Core Loader
Single Source of Truth Reader for Python Applications
"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Constants
DEFAULT_CORE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.json')

@dataclass
class MarkupTier:
    min_wholesale: float
    markup_percent: float

@dataclass
class DemandTier:
    max_price: float
    demand: float

@dataclass
class SeasonalFactors:
    factors: Dict[str, float]
    
    def get(self, month: str) -> float:
        return self.factors[month.lower()]

@dataclass
class ShippingConfig:
    cost_per_kg: float
    cost_per_m3: float
    max_weight_kg: float
    max_volume_m3: float
    crosses_border: bool
    customs_duty_rate: float
    days_transit: int

@dataclass
class WarehouseConfig:
    capacity_m3: float
    monthly_budget: float

@dataclass
class PathConfig:
    data_output: str
    product_candidates_csv: str
    final_catalog_csv: str
    
    def get_full_path(self, filename: str, core_file_path: str = DEFAULT_CORE_PATH) -> str:
        """
        Resolve path relative to the config.json location.
        If paths in JSON are like "../data/output", they are relative to the config/ folder.
        """
        if not os.path.isabs(self.data_output):
            # Anchor relative paths to the directory containing config.json
            config_dir = os.path.dirname(os.path.abspath(core_file_path))
            target_dir = os.path.normpath(os.path.join(config_dir, self.data_output))
        else:
            target_dir = self.data_output
            
        return os.path.join(target_dir, filename)

@dataclass
class ParameterCore:
    """Master configuration object"""
    version: str
    markup_tiers: List[MarkupTier]
    demand_tiers: List[DemandTier]
    seasonal_factors: SeasonalFactors
    shipping: ShippingConfig
    warehouse: WarehouseConfig
    paths: PathConfig
    optimization_defaults: Dict # Extra bucket for things like planning_months if not in JSON

def load_parameter_core(json_path: str = DEFAULT_CORE_PATH) -> ParameterCore:
    """
    Load the Parameter Core JSON file.
    Raises KeyError if required fields are missing (Fail Fast).
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Config file not found at: {json_path}")
        
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    try:
        # 1. Meta
        version = data['meta_info']['version']
        
        # 2. Economics
        econ = data['economics']
        markup_tiers = [MarkupTier(**t) for t in econ['markup_tiers']]
        demand_tiers = [DemandTier(**t) for t in econ['demand_model']['tiers']]
        seasonal = SeasonalFactors(factors=econ['seasonal_factors'])
        
        # 3. Logistics
        log = data['logistics']
        ship_data = log['shipping']
        shipping = ShippingConfig(
            cost_per_kg=ship_data['cost_per_kg'],
            cost_per_m3=ship_data['cost_per_m3'],
            max_weight_kg=ship_data['max_weight_kg'],
            max_volume_m3=ship_data['max_volume_m3'],
            crosses_border=ship_data['crosses_border'],
            customs_duty_rate=ship_data['customs_duty_rate'],
            days_transit=ship_data['days_transit']
        )
        
        ware_data = log['warehouse']
        warehouse = WarehouseConfig(
            capacity_m3=ware_data['capacity_m3'],
            monthly_budget=ware_data['monthly_budget']
        )
        
        # 4. Paths
        sys_paths = data['system_paths']
        paths = PathConfig(
            data_output=sys_paths['data_output'],
            product_candidates_csv=sys_paths['product_candidates_csv'],
            final_catalog_csv=sys_paths['final_catalog_csv']
        )
        
        # 5. Optimization Defaults
        optimization_defaults = data['optimization_defaults']
        
        return ParameterCore(
            version=version,
            markup_tiers=markup_tiers,
            demand_tiers=demand_tiers,
            seasonal_factors=seasonal,
            shipping=shipping,
            warehouse=warehouse,
            paths=paths,
            optimization_defaults=optimization_defaults
        )
        
    except KeyError as e:
        raise KeyError(f"Missing required key in Config JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to parse Parameter Core: {e}")

if __name__ == "__main__":
    # Test load
    try:
        core = load_parameter_core()
        print(f"Successfully loaded Parameter Core v{core.version}")
        print(f"Shipping Cost: ${core.shipping.cost_per_kg}/kg")
        print(f"Budget: ${core.warehouse.monthly_budget}")
        print(f"Paths resolved: {core.paths.get_full_path('test.csv')}")
    except Exception as e:
        print(f"Error: {e}")
