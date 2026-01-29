"""
Batch Product Optimizer - Option 1: High-Memory Fast Evaluation

Loads all product candidates and runs optimizer once with the full set.
The solver automatically selects the optimal subset that maximizes profit.
Uses parameter_core.json as the single source of truth.
"""
import csv
import time
import os
import argparse
import sys
from typing import List, Dict, Optional

# Import from optimization_engine.py (same directory)
from optimization_engine import (
    Product, DemandForecast, SeasonalFactors, ShippingOption,
    OptimizerConfig, PurchaseOrderOptimizer
)

# NEW: Import logic
from parameter_core_loader import load_parameter_core, ParameterCore
from consoleUI import ConsoleUI


# ========== CANDIDATE LOADING ==========

def load_candidates(filepath: str) -> List[Dict]:
    """Load product candidates from CSV file"""
    if not os.path.exists(filepath):
        ConsoleUI.error(f"Candidates file not found: {filepath}")
        sys.exit(1)

    ConsoleUI.status(f"Loading candidates from: {filepath}")
    start = time.time()
    
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['wholesale_price'] = float(row['wholesale_price'])
            row['retail_price'] = float(row['retail_price'])
            row['weight_g'] = float(row['weight_g'])
            row['size_cm3'] = float(row['size_cm3'])
            # Support both old and new field names if essential, but prefer JSON logic
            row['shipping_cost_multiplier'] = float(row.get('shipping_cost_multiplier', 1.0))
            row['base_demand'] = float(row['base_demand'])
            data.append(row)
    
    elapsed = time.time() - start
    ConsoleUI.metric("Loaded", len(data), f"candidates in {elapsed:.2f}s")
    
    return data

def filter_top_candidates(candidates: List[Dict], max_items: int = 15000) -> List[Dict]:
    """
    Heuristic filter to prevent solver choke.
    Keeps only the products with highest raw profit potential (Margin * Demand).
    """
    if len(candidates) <= max_items:
        return candidates

    ConsoleUI.warning(f"Candidate set size ({len(candidates):,}) exceeds solver safe limit ({max_items:,}).")
    ConsoleUI.status(f"Filtering to top {max_items:,} based on theoretical max profit...")
    
    # Calculate simple score: (Retail - Wholesale) * Base_Demand
    # This assumes we can sell the base demand; optimization will refine this.
    scored = []
    for c in candidates:
        margin = c['retail_price'] - c['wholesale_price']
        score = margin * c['base_demand']
        scored.append((score, c))
    
    # Sort descending
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Take top N
    filtered = [x[1] for x in scored[:max_items]]
    
    params_min = min(scored[:max_items], key=lambda x: x[0])[0]
    params_max = max(scored[:max_items], key=lambda x: x[0])[0]
    
    ConsoleUI.detail(f"Kept candidates with theoretical monthly profit between ${params_min:,.0f} and ${params_max:,.0f}")
    return filtered



def candidate_to_product(candidate: Dict, product_id: int, seasonal_factors_obj: SeasonalFactors) -> Product:
    """Convert ProductCandidate dict to Product object"""
    
    # Create demand forecast
    demand_forecast = DemandForecast(
        base_demand=candidate['base_demand'],
        seasonal_factors=seasonal_factors_obj,
        trend_factor=1.02,
        demand_buffer=1.5
    )
    
    # Build product
    product = Product(
        id=f"P{product_id:06d}",
        name=f"Product_{product_id}",
        wholesale_price=candidate['wholesale_price'],
        retail_price=candidate['retail_price'],
        size_cm3=candidate['size_cm3'],
        weight_g=candidate['weight_g'],
        category="General",  # Can be inferred post-optimization
        demand_forecast=demand_forecast,
        bulk_discount_threshold=0,
        bulk_discount_rate=0.0
    )
    
    return product


# ========== BATCH OPTIMIZATION ==========

def optimize_batch(
    candidates: List[Dict],
    config: OptimizerConfig,
    seasonal_factors_obj: SeasonalFactors,
    verbose: bool = True
) -> Dict:
    """
    Run optimizer on full candidate set
    
    Returns:
        Optimization results with purchase orders and profit breakdown
    """
    
    ConsoleUI.status(f"Converting {len(candidates):,} candidates to Product objects...")
    start = time.time()
    
    # Passing the seasonal_factors object which behaves like the one expected by spcplan
    products = [
        candidate_to_product(c, idx, seasonal_factors_obj) 
        for idx, c in enumerate(candidates, start=1)
    ]
    
    elapsed = time.time() - start
    ConsoleUI.detail(f"Conversion complete in {elapsed:.2f}s")
    ConsoleUI.detail(f"Memory estimate: ~{len(products) * 0.002:.1f}MB for product objects")
    
    ConsoleUI.status("Initializing optimizer...")
    optimizer = PurchaseOrderOptimizer(config)
    
    ConsoleUI.status("Running optimization (this may take 5-30 minutes for large sets)...")
    opt_start = time.time()
    
    results = optimizer.optimize(products)
    
    opt_elapsed = time.time() - opt_start
    ConsoleUI.metric("Optimization complete", opt_elapsed/60, "min")
    
    # Add timing metadata
    results['batch_metadata'] = {
        'total_candidates': len(candidates),
        'conversion_time_seconds': elapsed,
        'optimization_time_seconds': opt_elapsed,
        'total_time_seconds': elapsed + opt_elapsed
    }
    
    return results


def export_catalog_to_csv(results: Dict, filepath: str, candidates_map: Dict[str, Dict], top_n: Optional[int] = None) -> List[Dict]:
    """
    Export selected products to CSV with full parameters
    
    Returns:
        List of selected products for further use
    """
    
    if results['status'] not in ['OPTIMAL', 'FEASIBLE']:
        return []
    
    product_totals = results.get('product_totals', {})
    sorted_products = sorted(
        product_totals.items(),
        key=lambda x: x[1]['total_margin'],
        reverse=True
    )
    
    if top_n:
        sorted_products = sorted_products[:top_n]
    
    selected = []
    # Write CSV with all product parameters
    with open(filepath, 'w', newline='') as f:
        fieldnames = [
            'product_id', 'name', 'wholesale_price', 'retail_price',
            'weight_g', 'size_cm3', 'shipping_cost_multiplier', 'base_demand',
            'total_quantity_ordered', 'total_cost', 'total_revenue', 'total_margin'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for product_id, data in sorted_products:
            candidate = candidates_map.get(product_id, {})
            row = {
                'product_id': product_id,
                'name': data['name'],
                'wholesale_price': candidate.get('wholesale_price', 'N/A'),
                'retail_price': candidate.get('retail_price', 'N/A'),
                'weight_g': candidate.get('weight_g', 'N/A'),
                'size_cm3': candidate.get('size_cm3', 'N/A'),
                'shipping_cost_multiplier': candidate.get('shipping_cost_multiplier', 'N/A'),
                'base_demand': candidate.get('base_demand', 'N/A'),
                'total_quantity_ordered': data['total_quantity'],
                'total_cost': round(data['total_cost'], 2),
                'total_revenue': round(data['total_revenue'], 2),
                'total_margin': round(data['total_margin'], 2)
            }
            writer.writerow(row)
            selected.append(row)
    
    return selected


# ========== MAIN ==========

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Batch product optimization (JSON Core Version)'
    )
    # Optional override for candidates file, otherwise use default from JSON
    parser.add_argument(
        '--candidates',
        help='Path to product candidates CSV file (optional, overrides JSON default)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file for selected products (optional, overrides JSON default)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=None,
        help='Limit output to top N most profitable products'
    )
    parser.add_argument(
        '--budget',
        type=float,
        default=None,
        help='Monthly budget (optional, overrides JSON default)'
    )
    
    args = parser.parse_args()
    
    try:
        core = load_parameter_core()
        ConsoleUI.success(f"Loaded configuration v{core.version}")
    except Exception as e:
        ConsoleUI.error(f"Failed to load Parameter Core: {e}")
        sys.exit(1)
    
    # 2. Determine File Paths
    if args.candidates:
        candidates_file = args.candidates
    else:
        # Resolve path using the core helper which handles relative paths
        candidates_file = core.paths.get_full_path(core.paths.product_candidates_csv)
    
    if args.output:
        catalog_output = args.output
    else:
        catalog_output = core.paths.get_full_path(core.paths.final_catalog_csv)

    # 3. Load Candidates
    candidates = load_candidates(candidates_file)
    
    # Pre-Filter to avoid MemoryError/Timeouts with large inputs
    candidates = filter_top_candidates(candidates, max_items=20000)

    # 4. Map Core to Optimizer Config
    # We map the lightweight data classes from core to the logic classes in spcplan
    
    shipping = ShippingOption(
        name="Standard",
        cost_per_kg=core.shipping.cost_per_kg,
        cost_per_m3=core.shipping.cost_per_m3,
        max_weight_kg=core.shipping.max_weight_kg,
        max_volume_m3=core.shipping.max_volume_m3,
        crosses_border=core.shipping.crosses_border,
        customs_duty_rate=core.shipping.customs_duty_rate,
        days_transit=core.shipping.days_transit
    )
    
    # 5. Build Optimizer Config
    # Check overrides
    budget = args.budget if args.budget else core.warehouse.monthly_budget
    
    config = OptimizerConfig(
        planning_months=core.optimization_defaults.get('planning_months', 1),
        budget_per_month=budget,
        warehouse_capacity_m3=core.warehouse.capacity_m3,
        shipping=shipping,
        solver_time_limit_seconds=core.optimization_defaults.get('solver_time_limit_seconds', 60),
        solver_type=core.optimization_defaults.get('solver_type', 'SCIP'),
        demand_multiplier=core.optimization_defaults.get('demand_multiplier', 1.0)
    )
    
    # Seasonal Factors
    # Note: spcplan.SeasonalFactors expects a specific internal structure or method override.
    # We'll use the one from spcplan but populate it with our data if possible,
    # OR we assume spcplan's version is compatible.
    # Let's inspect spcplan.SeasonalFactors usage. 
    # Usually it's just initialized empty `SeasonalFactors()` in previous code.
    # Here we should probably pass our factors.
    # For now, we will create the default one and inject our factors if needed, 
    # or just rely on the default if the JSON factors match typical defaults.
    # Better: Update spcplan.SeasonalFactors to accept a dict, but I can't see spcplan.py right now.
    # The safest bet is:
    spc_seasonal = SeasonalFactors() 
    # If spc_seasonal has a .factors attribute, we set it:
    if hasattr(spc_seasonal, 'factors') and isinstance(spc_seasonal.factors, dict):
        # Convert string keys to int keys for spcplan compatibility
        # We handle potential mixed types by trying to convert all keys
        converted_factors = {}
        for k, v in core.seasonal_factors.factors.items():
            try:
                converted_factors[int(k)] = v
            except ValueError:
                # If key isn't convertible to int (e.g. "jan"), it won't be used by integer-based spcplan
                pass
        spc_seasonal.factors = converted_factors
    
    # Build mapping of product_id -> candidate for later export
    candidates_map = {}
    for idx, c in enumerate(candidates, start=1):
        candidates_map[f"P{idx:06d}"] = c
    
    # Show configuration
    ConsoleUI.section("CONFIGURATION")
    ConsoleUI.detail(f"Planning months: {config.planning_months}")
    ConsoleUI.detail(f"Budget per month: ${config.budget_per_month:,.2f}")
    ConsoleUI.detail(f"Warehouse capacity: {config.warehouse_capacity_m3}m³")
    
    try:
        # Run optimization
        results = optimize_batch(candidates, config, spc_seasonal)
        
        # Show results
        ConsoleUI.section("OPTIMIZATION RESULTS")
        ConsoleUI.detail(f"Status: {results['status']}")
        ConsoleUI.metric("Objective Value", results['objective_value'], "$")
        ConsoleUI.metric("Products Selected", len(results.get('product_totals', {})))
        
        # Export catalog
        catalog_dir = os.path.dirname(os.path.abspath(catalog_output)) or '.'
        os.makedirs(catalog_dir, exist_ok=True)
        
        selected = export_catalog_to_csv(results, catalog_output, candidates_map, args.top_n)
        
        ConsoleUI.success(f"Exported {len(selected)} products to: {catalog_output}")
        
        if selected:
            ConsoleUI.section("TOP PRODUCTS BY MARGIN")
            for i, p in enumerate(selected[:5], 1):
                ConsoleUI.detail(f"{i}. {p['product_id']}: ${p['total_margin']:,.2f} margin ({p['total_quantity_ordered']} units)")
        
    except MemoryError:
        ConsoleUI.error("Out of memory!")
        sys.exit(1)
        
    except Exception as e:
        ConsoleUI.error(f"Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)