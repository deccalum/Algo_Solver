import csv
import os
from dataclasses import dataclass, asdict
from enum import Enum, auto
from typing import Dict, Any, List
from glob import glob


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
        
        # Parse transit: handle both "PALLET" and "Transits.PALLET" formats
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


@dataclass
class Space:
    price_constraint: float
    space_constraint: float


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