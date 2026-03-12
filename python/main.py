from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.generator import ProductGenerator
from core.solver import ProcurementOptimizer, SolverConfig
from config.dev_default import build_dev_default

def main():
    config = build_dev_default()
    generator = ProductGenerator.from_proto_config(config)
    products = generator.generate()

    optimizer = ProcurementOptimizer(
        SolverConfig(
            budget_constraint=config.generation.budget,
            space_constraint=config.generation.space,
        )
    )
    optimization = optimizer.optimize(products)

    print(f"Generated {len(products)} products")
    if products:
        print(f"First: {products[0]}")
        print(f"Last:  {products[-1]}")
    print(f"Optimization status: {optimization.get('status', 'UNKNOWN')}")
    print(f"Objective value: {optimization.get('objective_value', 0.0)}")
    print(f"Selected products: {len(optimization.get('product_totals', {}))}")

if __name__ == "__main__":
    main()