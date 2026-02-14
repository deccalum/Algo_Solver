import os
import time

from common import Product, Space, PRICE_CONSTRAINTS, SPACE_CONSTRAINTS, load_products, export_products, export_results
import generator
from solver import Optimizer

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print(">>> Algo Solver Pipeline <<<")
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    # 1. GENERATION PHASE
    print("\n--- Phase 1: Product Generation ---")
    products = generator.generate_products()
    print(f"Generated {len(products)} products.")
    
    gen_filename = f"{script_name}_generated_{timestamp}.csv"
    gen_path = os.path.join(PROJECT_ROOT, "data", "output", gen_filename)
    export_products(products, gen_path)
    print(f"Saved generated products to: {gen_path}")

    # 2. OPTIMIZATION PHASE
    print("\n--- Phase 2: Optimization ---")
    print(f"Constraints: Budget=${PRICE_CONSTRAINTS}, Space={SPACE_CONSTRAINTS}")
    
    constraints = Space(price_constraint=PRICE_CONSTRAINTS, space_constraint=SPACE_CONSTRAINTS)
    optimizer = Optimizer(constraints=constraints)
    
    start_time = time.time()
    results = optimizer.optimize(products)
    duration = time.time() - start_time
    
    print(f"Optimization finished in {duration:.4f}s")
    print(f"Status: {results['status']}")
    
    if results['status'] in ['OPTIMAL', 'FEASIBLE']:
        print(f"Objective Value: {results['objective_value']:.2f}")
        
        opt_filename = f"{script_name}_optimized_{timestamp}.csv"
        opt_path = os.path.join(PROJECT_ROOT, "data", "output", opt_filename)
        export_results(results, opt_path)
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()


    
    
    # ISSUES
    # SOLVER PATHS (more generation)
    
        # # Competitor Model:
        # - High competition reduces effective demand.
        # - Competition intensity could be modeled as a function of product popularity (demand) 
        #   and ease of entry (low price/size).
        
        
        # def calculate_competition(price: float, size: float, demand: float) -> float:
        #     # Higher demand attracts more competitors (0.0 to 1.0 penalty)
        #     # Lower barriers (price/size) increase competition
        #     barrier_score = (math.log10(max(1.0, price)) + math.log10(max(1.0, size))) / 10.0
        #     comp_factor = (demand / 2000.0) * (1.0 - min(0.9, barrier_score))
        #     return max(0.1, 1.0 - min(0.8, comp_factor))
        
        #######################################################
        
        # Bathing/Volume Discounts:
        # - Suppliers may offer discounts for larger orders, affecting the effective price.
        # - Could model as a function of quantity thresholds and discount rates.
        
        # LOGISTICS_SOLVER:
        # threshold for logistics (truck, plane, shipping container)
        # If size exceeds threshold, logistics cost jumps significantly.
    
        #########################################################
        
        # Product Relationships:
        # - Some products may be complementary (buying one increases demand for another) or substitutable (buying one decreases demand for another).
        # - Could model as a graph of product interactions, affecting demand calculations.