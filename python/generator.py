import itertools
import math
import os
import random
import time
from typing import List, Dict, Any

from common import Product, export_products

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORE: Dict[str, Any] = {
        "price": [
            { "start": 1, "end": 100, "step": 5 },
            { "start": 100, "end": 1000, "step": 50 },
            { "start": 1000, "end": 10000, "step": 500 }
        ],
        "size": [
            { "start": 10, "end": 1000, "step": 50 },
            { "start": 1000, "end": 10000, "step": 500 },
            { "start": 10000, "end": 50000, "step": 2500 }
        ],
        "demand_model": {
            "demand": 1.0,
            "demand_decay": 0.0006,
            "min_price": 1.0,
            "size_decay": 20000.0,
            "noise": 0.15
        },
        "logistics_model": {
            "base_cost": 5.0,
            "size_multiplier": 0.01,
            "customs_duty_rate": 0.05
        },
        "markup_model": {
            "base_rate": 0.05,
            "price_scale": 0.35,
            "max_rate": 0.6,
            "noise": 0.12
        },
        "quantity_model": {
            "infinite_base_prob": 0.45,
            "infinite_price_scale": 350.0,
            "infinite_size_scale": 20000.0,
            "infinite_amount_base": 25000.0,
            "infinite_amount_price_scale": 500.0,
            "finite_base": 600.0,
            "finite_price_scale": 60.0,
            "finite_size_scale": 12000.0,
            "noise": 0.2
        }
    }


def demand_slope(price: float, size: float, economics: Dict) -> float:
    """Demand multiplier in the 0-1 range using exponential decay."""
    
    k = economics['demand_model']['demand_decay']
    min_price = economics['demand_model']['min_price']
    base_demand = economics['demand_model']['demand']
    size_decay = economics['demand_model']['size_decay']
    noise = economics['demand_model']['noise']
    
    # modifier = exp(-k * (price - min_price))
    demand = base_demand * math.exp(-k * (price - min_price))
    demand = demand * math.exp(-(size / max(1.0, size_decay)))
    demand = demand * random.uniform(1.0 - noise, 1.0 + noise)
    return max(0.01, min(0.99, demand))
    
    
def calculate_markup(price: float) -> float:
    """
    Markup rate in the 0-1 range.
    Low price items -> low margin
    High price items -> higher margin
    """
    model = CORE["markup_model"]
    base_rate = model["base_rate"]
    scale = model["price_scale"]
    max_rate = model["max_rate"]
    noise = model["noise"]

    price_factor = math.log10(max(1.0, price)) / 4.0
    rate = base_rate + (price_factor * scale)
    rate = min(max_rate, max(0.01, rate))
    rate = rate * random.uniform(1.0 - noise, 1.0 + noise)
    return max(0.01, min(0.99, rate))


def calculate_logistics(size: float) -> float:
    """
    Logistics difficulty curve (0.0 to 1.0).
    Realism:
    - Small items (needles, screws): High 'fiddly' factor. Easy to lose, hard to count.
    - Sweet spot (shoe box to microwave size): Standard shipping, automated handling. Lowest cost.
    - Large items (furniture, cars): Require special equipment (forklifts), expensive storage.
    
    Implementation:
    - We look for a U-shaped curve. 
    - Used a quadratic penalty based on the log-distance from the optimal size.
    """
    
    # Parameters for the curve
    optimal_size = 2000.0  # The size with the lowest logistics cost
    
    log_size = math.log10(max(1.0, size))
    log_opt = math.log10(optimal_size)
    
    # Calculate distance from optimal size in log space
    diff = log_size - log_opt
    
    # Quadratic penalty
    penalty = 0.15 * (diff ** 2)
    
    base_cost = 0.05
    val = base_cost + penalty
    
    return min(0.95, val) 


def generate_max_quantity(price: float, size: float) -> int:
    """
    Stock/Supply Limit.
    Realism: 
    - Commodities (low price, variable size) often have 'infinite' supply (limited only by budget).
    - Specialized/Luxury goods (high price) have scarce supply (limited by factory output/rarity).
    - Bulky goods are limited by physical warehouse space (though simulated here as abstract count).
    
    Implementation:
    - 30% chance of 'Infinite' supply (represented as a number larger than budget could ever buy).
    - Otherwise, supply constrained inversely by price (scarcity).
    """
    
    qm = CORE["quantity_model"]
    noise = qm["noise"]

    # Exponentially decaying chance of "infinite" supply as price/size rise.
    prob = qm["infinite_base_prob"]
    prob *= math.exp(-price / qm["infinite_price_scale"])
    prob *= math.exp(-size / qm["infinite_size_scale"])
    prob = max(0.0, min(1.0, prob))

    if random.random() < prob:
        amount = qm["infinite_amount_base"] * math.exp(-price / qm["infinite_amount_price_scale"])
        amount = amount * random.uniform(1.0 - noise, 1.0 + noise)
        return max(1, int(amount))

    # Finite supply decays exponentially with price and size.
    base = qm["finite_base"]
    count = base * math.exp(-price / qm["finite_price_scale"])
    count *= math.exp(-size / qm["finite_size_scale"])
    count = count * random.uniform(1.0 - noise, 1.0 + noise)
    return max(1, int(count))


def generate_bucketed_range(buckets: List[Dict]) -> List[float]:
    """Generate a non-linear range composed of multiple linear segments (buckets)"""
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

def generate_products(core: Dict = CORE) -> List[Product]:
    products = []
    price = generate_bucketed_range(core['price'])
    size = generate_bucketed_range(core['size'])
    
    for idx, (p, s) in enumerate(itertools.product(price, size), start=1):
        d = demand_slope(p, s, core)
        l = calculate_logistics(s)
        m = calculate_markup(p)
        q = generate_max_quantity(p, s)
        
        products.append(Product(
            id=f"P{idx:06d}",
            price=p,
            size=s,
            logistics=round(l, 3),
            demand=round(d, 3),
            markup=round(m, 3),
            max_quantity=q
        ))
        
    return products

if __name__ == "__main__":
    products = generate_products()
    
    out_dir = os.path.join(PROJECT_ROOT, "data", "output")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    out_path = os.path.join(out_dir, f"{script_name}_{timestamp}.csv")
    
    export_products(products, out_path)
