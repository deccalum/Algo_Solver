import csv
import os
import yaml
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from typing import Dict, Any, List, Optional
from glob import glob


def log(component: str, message: str):
    timestamp = __import__('time').strftime("%H:%M:%S")
    print(f"[{component} {timestamp}] {message}")


def format_price(value: float) -> str:
    """Format price with dollar sign and thousands separator: $X XXX.XX"""
    return f"${value:,.2f}".replace(',', ' ')


def format_number(value: float) -> str:
    """Format large numbers with thousands separator: X XXX"""
    if value == int(value):
        return f"{int(value):,}".replace(',', ' ')
    return f"{value:,.2f}".replace(',', ' ')


def format_volume(value: float) -> str:
    """
    Format volume with cm³/m³ units and smart conversion.
    Uses m³ for values >= 1000000 cm³ (1 m³), otherwise cm³.
    """
    if value >= 1_000_000:
        m3_value = value / 1_000_000
        return f"{format_number(m3_value)} m³"
    return f"{format_number(value)} cm³"


def _require_dict(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid config section: {name}")
    return value


def _require_float(section: Dict[str, Any], key: str, section_name: str) -> float:
    value = section.get(key)
    if value is None:
        raise ValueError(f"Missing required config key: {section_name}.{key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {section_name}.{key}: {value}") from exc

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load YAML configuration file using standard yaml.safe_load.
    Supports full YAML syntax including lists, maps, and nested structures.
    """
    if path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, '..', 'config', 'app.yaml')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        loaded = yaml.safe_load(f)
    return _require_dict(loaded, 'root')


@dataclass
class SolverConfig:
    """Default solver constraints loaded from app.yaml."""
    budget_constraint: float = field(init=False)
    space_constraint: float = field(init=False)

    def __post_init__(self):
        cfg = load_config()
        solver_section = _require_dict(cfg.get('solver'), 'solver')
        defaults = _require_dict(solver_section.get('default'), 'solver.default')
        self.budget_constraint = _require_float(defaults, 'budget', 'solver.default')
        self.space_constraint = _require_float(defaults, 'space', 'solver.default')


class Transits(Enum):
    COURIER =   auto()
    CONTAINER = auto()
    PALLET =    auto()
    
    
@dataclass
class Product:
    id:         str
    price:      float
    size:       float
    demand:     float
    markup:     float
    logistics:  float
    transit:    Transits
    transit_size: float 
    transit_cost: float 
    stock:      int 

    @staticmethod
    def from_row(row: Dict[str, Any], index: int) -> "Product":
        """Factory method to create Product from CSV row."""
        product_id = row.get("product_id", f"P{index:06d}")
        transit_str = row.get("transit", "COURIER")
        if "Transits." in transit_str:
            transit_str = transit_str.replace("Transits.", "")
        transit_enum = Transits[transit_str.upper()]
        
        return Product(
            id=product_id,
            price=float(row["price"]),
            size=float(row["size"]),
            logistics=float(row["logistics"]),
            demand=float(row["demand"]),
            markup=float(row.get("markup", 1.0)),
            stock=int(float(row.get("stock", 0))),
            transit=transit_enum,
            transit_size=float(row.get("transit_size", 0.0)),
            transit_cost=float(row.get("transit_cost", 0.0))
        )


class ProductRepository:
    """Centralized product data access and discovery."""
    
    @staticmethod
    def get_output_dir() -> str:
        """Return the standard output directory."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, "data", "output")
    
    @staticmethod
    def find_latest_generated() -> str:
        """
        Find the most recently generated product CSV.
        
        Returns:
            Filepath of the latest generator_*.csv file
            
        Raises:
            FileNotFoundError: If no generated files exist
        """
        output_dir = ProductRepository.get_output_dir()
        pattern = os.path.join(output_dir, "generator_*.csv")
        candidates = glob(pattern)
        
        if not candidates:
            raise FileNotFoundError(
                f"No generated products found in {output_dir}. "
                "Run generator.py first to create products."
            )
        
        latest_path: str = max(candidates, key=os.path.getmtime)
        return latest_path
    
    @staticmethod
    def load_products(filepath: str | None = None) -> List[Product]:
        """
        Load products from CSV.
        
        Args:
            filepath: Path to CSV file. If None, loads latest generated products.
            
        Returns:
            List of Product objects
        """
        if filepath is None:
            filepath = ProductRepository.find_latest_generated()
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Product file not found: {filepath}")
        products = []
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            products = [Product.from_row(row, i) for i, row in enumerate(reader, 1)]
        
        return products
    
    @staticmethod
    def export_products(products: List[Product], filepath: str):
        """Export products to CSV."""
        if not products:
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fieldnames = list(asdict(products[0]).keys())
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in products:
                writer.writerow(asdict(p))
        
        log("repo", f"Saved {len(products)} products to {os.path.basename(filepath)}")


    @staticmethod
    def export_results(results: Dict, filepath: str):
        """Export optimization results with quantities."""
        if results['status'] not in ['OPTIMAL', 'FEASIBLE']:
            log("repo", f"Skip export, optimization status is {results['status']}")
            return

        totals = results['product_totals']
        if not totals:
            log("repo", "Skip export, no selected products")
            return

        sorted_ids = sorted(totals.keys(), key=lambda x: totals[x].get('total_score', 0), reverse=True)
        first_item = totals[sorted_ids[0]]
        fieldnames = ['product_id'] + list(first_item.keys())
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for pid in sorted_ids:
                row = totals[pid].copy()
                row['product_id'] = pid
                writer.writerow(row)

        log("repo", f"Saved optimization results ({len(totals)} rows) to {os.path.basename(filepath)}")