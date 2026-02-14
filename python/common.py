import csv
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass
class Product:
    id: str
    price: float
    size: float
    logistics: float
    demand: float
    markup: float = 1.0
    max_quantity: int = 1

    @staticmethod
    def from_row(row: Dict[str, Any], index: int) -> "Product":
        product_id = row.get("product_id", f"P{index:06d}")
        return Product(
            id=product_id,
            price=float(row["price"]),
            size=float(row["size"]),
            logistics=float(row["logistics"]),
            demand=float(row["demand"]),
            markup=float(row["markup"]),
            max_quantity=int(float(row["quantity"])) if "quantity" in row else int(float(row["max_quantity"]))
        )

@dataclass
class Space:
    price_constraint: float
    space_constraint: float

# Default Constants
PRICE_CONSTRAINTS = 5000.0
SPACE_CONSTRAINTS = 1000000.0


# ========== SHARED I/O ==========

def load_products(filepath: str) -> List[Product]:
    if not os.path.exists(filepath):
        print(f"Error: File not found {filepath}")
        return []

    products = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        products = [Product.from_row(row, i) for i, row in enumerate(reader, 1)]
    return products

def export_products(products: List[Product], filepath: str):
    if not products: return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Generate fieldnames from the first product
    fieldnames = list(asdict(products[0]).keys())
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            writer.writerow(asdict(p))
    
    print(f"Exported {len(products)} products to {filepath}")


def export_results(results: Dict, filepath: str):
    """Export optimization results with quantities"""
    if results['status'] not in ['OPTIMAL', 'FEASIBLE']:
        print(f"Optimization failed with status: {results['status']}")
        return

    totals = results['product_totals']
    if not totals:
        print("No products selected.")
        return

    # Sort by score descending
    sorted_ids = sorted(totals.keys(), key=lambda x: totals[x]['score'], reverse=True)
    
    # Determine fields from first item
    first_item = totals[sorted_ids[0]]
    fieldnames = ['product_id'] + list(first_item.keys())
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for pid in sorted_ids:
            row = totals[pid]
            row['product_id'] = pid
            writer.writerow(row)

    print(f"Exported optimization results ({len(totals)} items) to {filepath}")

