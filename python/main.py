import os
import time

import generator
from common import ProductRepository
from solver import ProcurementOptimizer, SolverConfig

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print(">>> Algo Solver Pipeline <<<")
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    print(f"Script: {script_name}, Timestamp: {display_timestamp}")
    products = generator.generate_products()
    print(f"Generated {len(products)} products.")
    
    output_dir = ProductRepository.get_output_dir()
    gen_filename = f"generator_{timestamp}.csv"
    gen_path = os.path.join(output_dir, gen_filename)
    ProductRepository.export_products(products, gen_path)
    print(f"Saved generated products to: {os.path.basename(gen_path)}")

    budget = 100000.0
    space = 50000.0
    print(f"Constraints: Budget=${budget}, Space={space}")
    
    config = SolverConfig(budget_constraint=budget, space_constraint=space)
    optimizer = ProcurementOptimizer(config=config)
    start_time = time.time()
    results = optimizer.optimize(products)
    duration = time.time() - start_time
    
    print(f"Optimization finished in {duration:.4f}s")
    print(f"Status: {results['status']}")
    
    if results['status'] in ['OPTIMAL', 'FEASIBLE']:
        print(f"Objective Value: {results['objective_value']:.2f}")
        print(f"Selected Products: {len(results['selected_products'])}")
        output_dir = ProductRepository.get_output_dir()
        opt_filename = f"solver_optimized_{timestamp}.csv"
        opt_path = os.path.join(output_dir, opt_filename)
        ProductRepository.export_results(results, opt_path)
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()