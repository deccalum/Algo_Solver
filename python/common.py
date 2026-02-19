import csv
import os
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Dict, Any, List, Optional
from glob import glob

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses a simple YAML configuration file tailored for app.yaml structure.
    Handles nested keys, lists, and numeric types without external deps.
    """
    if path is None:
        # Resolve to ../config/app.yaml relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, '..', 'config', 'app.yaml')
    
    config = {}
    if not os.path.exists(path):
        print(f"Warning: Config file not found at {path}")
        return config

    # Stack to track nesting: (indent_level, dict_reference)
    stack = [(-1, config)]

    with open(path, 'r') as f:
        for line in f:
            raw_line = line.rstrip()
            if not raw_line or raw_line.strip().startswith('#'):
                continue

            stripped_line = raw_line.lstrip()
            indent = len(raw_line) - len(stripped_line)
            
            # Find parent level
            while stack and stack[-1][0] >= indent:
                stack.pop()

            parent = stack[-1][1]
            
            if ':' in stripped_line:
                key, value_str = stripped_line.split(':', 1)
                key = key.strip()
                value_str = value_str.strip()
                
                # New section
                if not value_str or value_str.startswith('#'):
                    new_section = {}
                    parent[key] = new_section
                    stack.append((indent, new_section))
                else:
                    # Parse value
                    if ' #' in value_str: value_str = value_str.split(' #')[0].strip()
                    
                    val = None
                    # Lists [a, b]
                    if value_str.startswith('[') and value_str.endswith(']'):
                        content = value_str[1:-1]
                        items = [x.strip() for x in content.split(',')]
                        parsed = []
                        for item in items:
                            try:
                                if '.' in item: parsed.append(float(item))
                                else: parsed.append(int(item))
                            except ValueError: parsed.append(item.strip('"\''))
                        val = parsed
                    # Primitives
                    else:
                        if value_str.lower() == 'true': val = True
                        elif value_str.lower() == 'false': val = False
                        else:
                            try:
                                if '.' in value_str: val = float(value_str)
                                else: val = int(value_str)
                            except ValueError: val = value_str.strip('"\'')
                    
                    parent[key] = val

    return config


@dataclass
class SolverConfig:
    """Default solver constraints, loaded from app.yaml if available."""
    budget_constraint: float = 50000.0
    space_constraint: float = 100000.0

    def __post_init__(self):
        # Wire to app.yaml
        cfg = load_config()
        try:
            defaults = cfg.get('solver', {}).get('default', {})
            if 'budget' in defaults: self.budget_constraint = float(defaults['budget'])
            if 'space' in defaults: self.space_constraint = float(defaults['space'])
        except Exception as e:
            print(f"Error applying config: {e}")


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
    transit_size: float = 0.0
    transit_cost: float = 0.0
    stock:      int = 0

    @staticmethod
    def from_row(row: Dict[str, Any], index: int) -> "Product":
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
        
        print(f"Exported {len(products)} products to {os.path.basename(filepath)}")


    @staticmethod
    def export_results(results: Dict, filepath: str):
        """Export optimization results with quantities."""
        if results['status'] not in ['OPTIMAL', 'FEASIBLE']:
            print(f"Optimization failed with status: {results['status']}")
            return

        totals = results['product_totals']
        if not totals:
            print("No products selected.")
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

        print(f"Exported optimization results ({len(totals)} items) to {os.path.basename(filepath)}")