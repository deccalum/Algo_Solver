"""
Candidate Generator - Parameter Core Integrated
Reads configuration from parameter_core.json and generates product candidates.
"""
import itertools
import json
import csv
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# ========== CORE CONFIGURATION LOADER ==========

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_FILE = os.path.join(PROJECT_ROOT, "config", "parameter_core.json")

def load_parameter_core() -> Dict[str, Any]:
    """Load the JSON parameter core"""
    if not os.path.exists(CORE_FILE):
        raise FileNotFoundError(f"Parameter core not found at: {CORE_FILE}")
    
    print(f"Loading core from: {CORE_FILE}")
    with open(CORE_FILE, 'r') as f:
        data = json.load(f)
        print(f"Loaded version: {data.get('meta_info', {}).get('version', 'unknown')}")
        return data

# ========== LOGIC ==========

def estimate_retail_price(wholesale: float, economics: Dict) -> float:
    """Calculate retail price based on markup tiers from JSON"""
    tiers = sorted(economics['markup_tiers'], key=lambda x: x['min_wholesale'], reverse=True)
    
    for tier in tiers:
        if wholesale >= tier['min_wholesale']:
            return wholesale * (1 + tier['markup_percent'])
            
    return wholesale * 1.5 # fallback

def estimate_base_demand(wholesale: float, economics: Dict) -> float:
    """Calculate demand based on price tiers from JSON"""
    tiers = sorted(economics['demand_model']['tiers'], key=lambda x: x['max_price'])
    
    for tier in tiers:
        if wholesale <= tier['max_price']:
            return tier['demand']
            
    return economics['demand_model']['tiers'][-1]['demand']

def is_realistic_combination(price: float, weight_kg: float, size_cm3: float, 
                              density_min: float = 0.01, density_max: float = 10.0) -> bool:
    """
    Filter out unrealistic product combinations using advanced heuristics.
    """
    # 1. Density Check (kg/L)
    volume_liters = size_cm3 / 1000.0
    density = weight_kg / volume_liters if volume_liters > 0 else 0
    
    if density < density_min or density > density_max:
        return False
        
    # 2. Value density Check ($/kg)
    value_per_kg = price / weight_kg if weight_kg > 0 else 0
    
    # Cheap heavy items (e.g. $5 10kg rock) - Shipping eats margin
    if price < 10 and weight_kg > 5:
        return False
        
    # Cheap bulky items (e.g. $5 huge styrofoam block) - Shipping volume eats margin
    if price < 5 and size_cm3 > 10_000:
        return False
        
    # Mid-range: Reasonable value density needed
    if 100 <= price <= 1000:
        # e.g. laptop ($800, 2kg) -> $400/kg. Good.
        # e.g. cheap furniture ($200, 50kg) -> $4/kg. Borderline but allowed.
        # e.g. bag of sand ($100, 100kg) -> $1/kg. Bad.
        if value_per_kg < 1.0:
            return False
            
    # Luxury: Should generally be high value density
    if price >= 1000:
        # Luxury furniture exists, so we can't be too strict, 
        # but pure industrial raw materials are out.
        if value_per_kg < 2.0:
            return False
            
    # 3. Size-Weight Anomalies
    # Huge but feather light (e.g. 50cm x 50cm x 50cm box weighing 100g)
    if size_cm3 > 50_000 and weight_kg < 0.2:
        return False
        
    # Tiny but super heavy (e.g. 10cm cube weighing 20kg - solid lead/gold?) -- unless expensive
    if weight_kg > 20 and size_cm3 < 2_000 and price < 500:
        return False
        
    return True

@dataclass
class ProductCandidate:
    wholesale_price: float
    retail_price: float
    weight_g: float
    size_cm3: float
    shipping_multiplier: float
    base_demand: float

def generate_bucketed_range(buckets: List[Dict]) -> List[float]:
    """
    Generate a non-linear range composed of multiple linear segments (buckets).
    """
    vals = set()
    for b in buckets:
        start = b['start']
        end = b['end']
        step = b['step']
        if step <= 0:
            vals.add(start)
            continue
        curr = start
        while curr <= end + (step/1000.0):
            vals.add(round(curr, 4))
            curr += step
    return sorted(list(vals))

def generate_candidates(core: Dict, verbose: bool = True) -> List[ProductCandidate]:
    gen_params = core['generation_parameters']
    econ_params = core['economics']
    
    # 1. Expand Ranges
    prices = generate_bucketed_range(gen_params['price_usd'])
    weights_kg = generate_bucketed_range(gen_params['weight_kg'])
    sizes = generate_bucketed_range(gen_params['size_cm3'])
    shipping = generate_bucketed_range(gen_params['shipping_multiplier'])
    
    if verbose:
        count = len(prices) * len(weights_kg) * len(sizes) * len(shipping)
        print(f"Generating from Parameter Core...")
        print(f" - Price Points: {len(prices)}")
        print(f" - Weight Points: {len(weights_kg)}")
        print(f" - Size Points: {len(sizes)}")
        print(f" - Search Space: {count:,} combinations")

    candidates = []
    
    d_min = gen_params['constraints']['density_kg_l']['min']
    d_max = gen_params['constraints']['density_kg_l']['max']
    
    # 2. Iterate
    for price, weight_kg, size, ship in itertools.product(prices, weights_kg, sizes, shipping):
        
        # Apply strict rules
        if not is_realistic_combination(price, weight_kg, size, d_min, d_max):
            continue
            
        retail = estimate_retail_price(price, econ_params)
        demand = estimate_base_demand(price, econ_params)
        weight_grams = weight_kg * 1000.0
        
        candidates.append(ProductCandidate(
            wholesale_price=price,
            retail_price=retail,
            weight_g=weight_grams, 
            size_cm3=size,
            shipping_multiplier=ship,
            base_demand=demand
        ))
        
    if verbose:
        print(f"Generated {len(candidates):,} valid candidates.")
        
    return candidates

def export_csv(candidates: List[ProductCandidate], filepath: str):
    if not candidates: return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=asdict(candidates[0]).keys())
        writer.writeheader()
        for c in candidates:
            writer.writerow(asdict(c))
            
    print(f"Exported to {filepath}")

if __name__ == "__main__":
    core = load_parameter_core()
    
    out_dir = core['system_paths']['data_output']
    filename = core['system_paths']['product_candidates_csv']
    out_path = os.path.join(PROJECT_ROOT, out_dir.replace('../', ''), filename)
    
    cands = generate_candidates(core)
    export_csv(cands, out_path)
