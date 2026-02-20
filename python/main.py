import os
import time

from generator import ProductGenerator
from common import ProductRepository, SolverConfig, log, format_price, format_number
from solver import ProcurementOptimizer

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    log("main", "Starting Algo Solver pipeline")
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    
    log("main", "Kicking off data generation")
    gen = ProductGenerator()
    products = gen.generate()
    log("main", f"Generation done. Products ready: {format_number(len(products))}")
    output_dir = ProductRepository.get_output_dir()
    gen_filename = f"generator_{timestamp}.csv"
    gen_path = os.path.join(output_dir, gen_filename)
    ProductRepository.export_products(products, gen_path)
    log("main", f"Generator output file: {os.path.basename(gen_path)}")

    log("main", "Starting optimizer")
    optimizer = ProcurementOptimizer(SolverConfig())
    start_time = time.time()
    results = optimizer.optimize(products)
    duration = time.time() - start_time
    log("main", f"Optimization finished in {duration:.4f}s")
    log("main", f"Status: {results['status']}")
    if results['status'] in ['OPTIMAL', 'FEASIBLE']:
        log("main", f"Objective value: {format_price(results['objective_value'])}")
        log("main", f"Selected products: {format_number(len(results['product_totals']))}")
        output_dir = ProductRepository.get_output_dir()
        opt_filename = f"solver_optimized_{timestamp}.csv"
        opt_path = os.path.join(output_dir, opt_filename)
        ProductRepository.export_results(results, opt_path)
        log("main", f"Optimizer output file: {os.path.basename(opt_path)}")
    else:
        log("main", "No feasible solution this run")

if __name__ == "__main__":
    main()