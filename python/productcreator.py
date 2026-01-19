"""
Product Parameter Optimization via Cartesian Product Enumeration

Generates all feasible combinations of product parameters.

"""
import itertools
import os
import csv
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

from config_models import AppConfig
from consoleUI import ConsoleUI


# ========== PARAMETERS ==========

@dataclass
class GenerationParams:
    """Parameters for product candidate generation"""
    
    # Price in USD
    price_min: float = 1
    price_max: float = 10_000
    price_step: float = 10
    
    # ⚠️ TODO: WEIGHT UNIT INCONSISTENCY
    # Weight is specified in GRAMS here, but functions like is_realistic_combination()
    # expect weight_kg (kilograms). This causes validation logic to fail.
    # MUST fix: either convert all to grams OR convert all to kg consistently.
    # Currently: ProductCandidate.weight_g is in grams, but calculations treat it as kg.
    #
    # ⚠️ TODO: WEIGHT GENERATION PROBLEM - UNREALISTIC INCREMENTS
    # Current linear step generation (weight_min + step, +step, ...) creates unrealistic
    # intermediate values. For example:
    # - Linear: [2g, 4g, 6g, 8g, ..., 100kg] has huge gaps and millions of combinations
    # - Real products don't follow linear weight distribution
    # SUGGESTED SOLUTIONS:
    #   1. Logarithmic: weights = [min * (max/min)^(i/n) for i in range(n)]
    #   2. Exponential: weights = [min * (ratio^i) for i in range(n)] where ratio = (max/min)^(1/n)
    #   3. Realistic buckets: [0-1g, 1-10g, 10-100g, 100-1kg, 1-10kg, ...]
    # DO NOT use until unit inconsistency is fixed.
    
    # Weight in grams
    weight_min: float = 2
    weight_max: float = 100_000
    weight_step: float = 2
    
    # Size in cm³
    size_min: float = 1
    size_max: float = 50_000
    size_step: float = 50
    
    # Shipping cost multipliers
    freight_min: float = 1.0
    freight_max: float = 5.0
    freight_step: float = 1.0
    
    # density constraints (kg/L)
    density_min: float = 0.01
    density_max: float = 10.0
    
    # Filter candidates by profit
    max_candidates: Optional[int] = None
    

@classmethod
def from_ui_input(cls, form_data: Dict) -> 'GenerationParams':
    """Create GenerationParams from UI form data"""
    return cls(
        price_min=float(form_data.get('price_min', 1)),
        price_max=float(form_data.get('price_max', 10_000)),
        price_step=float(form_data.get('price_step', 10)),
        weight_min=float(form_data.get('weight_min', 2)),
        weight_max=float(form_data.get('weight_max', 100_000)),
        weight_step=float(form_data.get('weight_step', 2)),
        size_min=float(form_data.get('size_min', 1)),
        size_max=float(form_data.get('size_max', 50_000)),
        size_step=float(form_data.get('size_step', 50)),
        density_min=float(form_data.get('density_min', 0.01)),
        density_max=float(form_data.get('density_max', 10.0)),
        max_candidates=int(form_data.get('max_candidates')) if form_data.get('max_candidates') else None,
        freight_min=float(form_data.get('freight_min', 1.0)),
        freight_max=float(form_data.get('freight_max', 5.0)),
        freight_step=float(form_data.get('freight_step', 1.0))
    )

# ========== PARAMETER RANGE GENERATORS ==========

def generate_price_range(min_price: float = 1, max_price: float = 10000, step: float = 1) -> List[float]:
        """Generate price range with absolute control"""
        prices = []
        current = min_price
        while current <= max_price:
            prices.append(round(current, 2))
            current += step
            
        return prices
    

def generate_weight_range(min_weight: float = 0.1, max_weight: float = 100, step: float = 0.1) -> List[float]:
    """
    Generate discrete weight points in GRAMS
    
    ⚠️ TODO: FIX THIS FUNCTION - generates unrealistic linear increments
    Current: Linear steps create millions of useless intermediate values
    Example: [0.1, 0.2, 0.3, ..., 100000] has 1M+ combinations
    
    IMPLEMENT ONE OF THESE APPROACHES:
    1. Logarithmic: np.logspace(log10(min), log10(max), n_steps)
    2. Exponential: [min * ratio^i for i in range(n)] where ratio = (max/min)^(1/n)
    3. Categorical: Real weight distribution by product type
    
    This dramatically impacts generate_all_product_candidates() output size.
    """
    weight_range = []
    current = min_weight
    while current <= max_weight:
        weight_range.append(round(current, 2))
        current += step
    return weight_range


def generate_size_range(min_size: float = 2, max_size: float = 50_000, step: float = 100) -> List[float]:
    """Generate discrete size points in cm³"""
    size_range = []
    current = min_size
    while current <= max_size:
        size_range.append(round(current, 2))
        current += step
    return size_range


def generate_shipping_costs(freight_min: float = 1.0, freight_max: float = 5.0, freight_step: float = 1.0) -> List[float]:
    """Discrete shipping cost multipliers"""
    shipping_costs = []
    current = freight_min
    while current <= freight_max:
        shipping_costs.append(round(current, 2))
        current += freight_step
    return shipping_costs


# ========== PRE-FILTER RULES ==========
# evaluate these functions...

def is_realistic_combination(price: float, weight_kg: float, size_cm3: float, 
                              density_min: float = 0.01, density_max: float = 10.0) -> bool:
    """
    Filter out unrealistic product combinations
    
    Args:
        price: Price in USD
        weight_kg: Weight in GRAMS (converted to kg internally)
        size_cm3: Size in cubic centimeters
        density_min: Minimum density in kg/L
        density_max: Maximum density in kg/L
    
    Rules:
    1. Density constraint: weight/volume must be physically reasonable
    2. Value density: cheap items shouldn't be huge/heavy
    3. Luxury items shouldn't be tiny/light (with exceptions)
    """
    
    # Convert grams to kilograms for calculations
    weight_kg = weight_kg / 1000.0
    
    # Calculate density (kg/L)
    volume_liters = size_cm3 / 1000.0
    density = weight_kg / volume_liters if volume_liters > 0 else 0
    
    # Rule 1: Physical density bounds (configurable)
    if density < density_min or density > density_max:
        return False
    
    # Rule 2: Value-to-weight ratio
    value_per_kg = price / weight_kg if weight_kg > 0 else 0
    
    # Cheap items ($1-$10) shouldn't exceed 5kg
    if price < 10 and weight_kg > 5:
        return False
    
    # Very cheap items ($1-$5) shouldn't exceed 10,000 cm³
    if price < 5 and size_cm3 > 10_000:
        return False
    
    # Mid-range items ($100-$1000) need reasonable value density
    if 100 <= price <= 1000:
        if value_per_kg < 10:  # Less than $10/kg is unrealistic for mid-range
            return False
    
    # Luxury items ($1000+) should have high value density
    if price >= 1000:
        if value_per_kg < 50:  # Less than $50/kg unlikely for luxury goods
            return False
        if size_cm3 > 30_000:  # Most luxury items aren't huge
            return False
    
    # Rule 3: Size-weight correlation
    # Extremely light but large items are rare (balloons, pillows - not typical online shop)
    if size_cm3 > 20_000 and weight_kg < 0.5:
        return False
    
    # Heavy but tiny items need high price (jewelry, electronics)
    if weight_kg > 10 and size_cm3 < 1_000 and price < 100:
        return False
    
    return True

#! consider changing this
def estimate_retail_price(wholesale: float, app_config: AppConfig) -> float:
    """
    Calculate retail price based on wholesale with tiered markup from config
    
    Lower-priced items: higher markup %
    Higher-priced items: lower markup %
    """
    for tier in app_config.markup_tiers:
        if tier.min_cost <= wholesale < tier.max_cost:
            return wholesale * tier.markup_multiplier
    
    # Fallback to last tier if price exceeds all bounds
    return wholesale * app_config.markup_tiers[-1].markup_multiplier


def get_demand_tier(price: float, app_config: AppConfig) -> Optional[object]:
    """Find the demand tier for a given price"""
    for tier in app_config.demand_tiers:
        if tier.min_price <= price < tier.max_price:
            return tier
    return None


def estimate_base_demand(wholesale: float, size_cm3: float, weight_kg: float, app_config: AppConfig) -> float:
    """
    Estimate monthly demand based on price tier with max_demand constraint
    
    Args:
        wholesale: Wholesale price in USD
        size_cm3: Product size in cubic centimeters
        weight_kg: Weight in GRAMS (converted to kg internally)
        app_config: Application configuration with demand tiers
    
    CRITICAL: This enforces realistic demand caps inversely proportional to price.
    - Cheap items: higher demand but NOT unlimited
    - Expensive items: lower demand with strict caps
    
    The max_demand constraint prevents the optimizer from ordering unrealistic
    quantities (e.g., 767 $800 laptops). Instead, luxury items max out around 20/month.
    """
    # Convert grams to kilograms for calculations
    weight_kg = weight_kg / 1000.0
    
    # Get demand tier from config based on wholesale price
    tier = get_demand_tier(wholesale, app_config)
    
    if tier is None:
        # Fallback if price is outside all tiers (shouldn't happen with proper config)
        return 5
    
    # Start with base demand for this tier
    base = tier.base_demand_monthly
    
    # Apply demand multiplier for this tier (product-specific elasticity)
    base = base * tier.demand_multiplier
    
    # Reduce demand for bulky/heavy items (harder to store/ship)
    if size_cm3 > 20_000:
        base *= 0.5
    if weight_kg > 20:
        base *= 0.7
    
    # Cap at maximum for this tier (THIS IS THE KEY CONSTRAINT)
    max_demand = tier.max_demand_monthly
    result = min(max(1, base), max_demand)
    
    return result


# ========== PRODUCT GENERATION ==========

@dataclass
class ProductCandidate:
    """Generated product candidate for evaluation"""
    wholesale_price: float
    retail_price: float
    weight_g: float
    size_cm3: float
    shipping_cost_multiplier: float
    base_demand: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


def generate_all_product_candidates(
    params: GenerationParams,
    app_config: AppConfig,
    verbose: bool = True
) -> List[ProductCandidate]:
    """Generate candidates with given parameters and filtering"""
    
    # Generate ranges with control
    prices = generate_price_range(
        params.price_min,
        params.price_max,
        params.price_step
    )
    weights = generate_weight_range(
        params.weight_min,
        params.weight_max,
        params.weight_step
    )
    sizes = generate_size_range(
        params.size_min,
        params.size_max,
        params.size_step
    )
    shipping_costs = generate_shipping_costs(
        params.freight_min,
        params.freight_max,
        params.freight_step
    )
    
    if verbose:
        ConsoleUI.metric("Price range", len(prices), "values")
        ConsoleUI.metric("Weight range", len(weights), "values")
        ConsoleUI.metric("Size range", len(sizes), "values")
        ConsoleUI.metric("Shipping options", len(shipping_costs), "multipliers")
    
    # Generate all combinations via cartesian product
    candidates = []
    total_combinations = len(prices) * len(weights) * len(sizes) * len(shipping_costs)
    
    if verbose:
        ConsoleUI.status(f"Generating {total_combinations:,} candidate combinations...")
    
    for price in prices:
        for weight in weights:
            for size in sizes:
                for shipping_mult in shipping_costs:
                    # Filter unrealistic combinations
                    if not is_realistic_combination(price, weight, size, params.density_min, params.density_max):
                        continue
                    
                    # Calculate derived attributes
                    retail_price = estimate_retail_price(price, app_config)
                    base_demand = estimate_base_demand(price, size, weight, app_config)
                    
                    # Create candidate
                    candidate = ProductCandidate(
                        wholesale_price=price,
                        retail_price=retail_price,
                        weight_g=weight,
                        size_cm3=size,
                        shipping_cost_multiplier=shipping_mult,
                        base_demand=base_demand
                    )
                    candidates.append(candidate)
    
    # Apply max_candidates limit if specified
    if params.max_candidates and len(candidates) > params.max_candidates:
        # Sort by profit potential and keep top N
        candidates.sort(
            key=lambda c: (c.retail_price - c.wholesale_price) * c.base_demand,
            reverse=True
        )
        candidates = candidates[:params.max_candidates]
    
    if verbose:
        ConsoleUI.success(f"Generated {len(candidates):,} valid candidates (filtered from {total_combinations:,})")
    
    return candidates

def export_candidates(candidates: List[ProductCandidate], filepath: str, app_config: AppConfig):
    """Export candidates to CSV only"""
    data = [c.to_dict() for c in candidates]
    # Ensure output directory exists
    output_dir = os.path.dirname(filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    if not data:
        ConsoleUI.warning(f"No candidates to export to {filepath}")
        return
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


# ========== MAIN ==========

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate product parameter combinations for optimization'
    )
    parser.add_argument(
        '--filter-mode',
        choices=['full', 'medium', 'aggressive'],
        default='full',
        help='Filter preset: full (~1.5M), medium (~100k), aggressive (~10k)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV file path (default: from config.cfg)'
    )
    args = parser.parse_args()
    
    # Load config for default paths
    app_config = AppConfig.from_cfg_file('config.cfg')
    output_file = args.output or os.path.join(app_config.paths.data_output_dir, app_config.paths.product_candidates_file)
    
    # Load preset
    preset = app_config.filter_presets[args.filter_mode]
    
    ConsoleUI.header("PRODUCT PARAMETER SPACE GENERATOR")
    ConsoleUI.detail(f"Filter Mode: {args.filter_mode.upper()} - {preset.description}")

    
    # Build GenerationParams from preset
    params = GenerationParams(
        price_min=1,
        price_max=preset.max_price,
        price_step=preset.price_steps if isinstance(preset.price_steps, (int, float)) else 10,
        weight_min=1,
        weight_max=preset.max_weight,
        weight_step=preset.weight_steps if isinstance(preset.weight_steps, (int, float)) else 1,
        size_min=1,
        size_max=preset.max_size,
        size_step=preset.size_steps if isinstance(preset.size_steps, (int, float)) else 100,
        density_min=preset.density_min,
        density_max=preset.density_max
    )
    
    # Generate all valid combinations with preset parameters
    candidates = generate_all_product_candidates(
        params=params,
        app_config=app_config,
        verbose=True
    )
    
    # Show sample candidates
    ConsoleUI.section("SAMPLE CANDIDATES (first 10)")
    for i, candidate in enumerate(candidates[:10], 1):
        margin = candidate.retail_price - candidate.wholesale_price
        margin_pct = (margin / candidate.retail_price * 100) if candidate.retail_price > 0 else 0
        ConsoleUI.detail(f"{i}. Wholesale: ${candidate.wholesale_price:.2f} → Retail: ${candidate.retail_price:.2f}")
        ConsoleUI.detail(f"   Margin: ${margin:.2f} ({margin_pct:.1f}%)")
        ConsoleUI.detail(f"   Weight: {candidate.weight_g/1000:.2f}kg, Size: {candidate.size_cm3:,.0f}cm³")
        ConsoleUI.detail(f"   Shipping: {candidate.shipping_cost_multiplier}x, Demand: {candidate.base_demand:.0f}/mo")
    
    # Export
    export_candidates(candidates, output_file, app_config)
    ConsoleUI.success(f"Exported {len(candidates):,} candidates to: {output_file}")
