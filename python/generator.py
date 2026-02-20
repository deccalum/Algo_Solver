"""
Cartesian Product Enumeration - Generate product catalog from config-driven models.

All configuration is loaded from variables.py. variables.py reads app.yaml.
"""
import itertools
import math
import os
import random
import time
import numpy as np
from typing import List, Protocol

import variables
from common import Transits, Product, dataclass, ProductRepository, log, format_price, format_number, format_volume

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class ZoneMode(Protocol):
    """Protocol for zone value generation strategies."""
    def generate(self, start: float, end: float, zone: "Zone") -> List[float]:
        ...


@dataclass
class ExactMode:
    """Generate values at exact step intervals."""
    def generate(self, start: float, end: float, zone: "Zone") -> List[float]:
        gr = variables.guardrails
        span = max(gr.min_span, end - start)
        step = max(gr.min_step, zone.step)
        count = max(int(span / step) + 1, gr.min_count)
        values = np.linspace(start, end, count)
        return [float(v) for v in values]


@dataclass
class PowerCurveMode:
    """Generate values along a power curve (bias controls concentration)."""
    def generate(self, start: float, end: float, zone: "Zone") -> List[float]:
        gr = variables.guardrails
        resolution = max(gr.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        shaped = t ** max(gr.min_bias, zone.bias)
        values = start + (end - start) * shaped
        return [float(v) for v in values]


@dataclass
class GeometricMode:
    """Generate values in geometric progression."""
    def generate(self, start: float, end: float, zone: "Zone") -> List[float]:
        gr = variables.guardrails
        resolution = max(gr.min_resolution, zone.resolution)
        safe_start = max(gr.min_safe_start, start)
        safe_end = max(safe_start, end)
        ratio = (safe_end / safe_start) ** (1.0 / (resolution - 1))
        values = [safe_start * (ratio ** i) for i in range(resolution)]
        return values


@dataclass
class UShapeMode:
    """Generate values with edge density (U-shaped distribution)."""
    def generate(self, start: float, end: float, zone: "Zone") -> List[float]:
        gr = variables.guardrails
        resolution = max(gr.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        edge_dense = 0.5 - 0.5 * np.cos(np.pi * t)
        values = start + (end - start) * edge_dense
        return [float(v) for v in values]


MODE_REGISTRY = {
    'exact': ExactMode(),
    'power': PowerCurveMode(),
    'geometric': GeometricMode(),
    'u_shape': UShapeMode(),
}


@dataclass
class Zone:
    """Zone configuration. Defines how to generate values within a price/size range."""
    mode: ZoneMode
    span_share: float
    resolution: int
    bias: float
    step: float


@dataclass
class DemandModel:
    """Demand probability model. Calculates demand based on price and size."""
    base_demand: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    noise: float
    min_demand: float
    max_demand: float
    
    def evaluate(self, price: float, size: float) -> float:
        """Calculate demand probability for given price and size."""
        price_norm = math.log10(max(1.0, price)) / math.log10(max(10.0, self.price_scale))
        size_norm = math.log10(max(1.0, size)) / math.log10(max(10.0, self.size_scale))
        demand_penalty = (self.price_sensitivity * price_norm) + (self.size_sensitivity * size_norm)
        demand = self.base_demand * math.exp(-demand_penalty)
        demand *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_demand, min(self.max_demand, demand))


@dataclass
class MarkupModel:
    """Markup/margin model. Calculates markup rate based on price."""
    base_rate: float
    price_scale: float
    max_rate: float
    noise: float
    price_divisor: float
    min_rate: float
    max_rate_clamp: float
    
    def evaluate(self, price: float) -> float:
        """Calculate markup rate for given price."""
        price_factor = math.log10(max(1.0, price)) / self.price_divisor
        rate = self.base_rate + (price_factor * self.price_scale)
        rate = min(self.max_rate, max(self.min_rate, rate))
        rate *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_rate, min(self.max_rate_clamp, rate))


@dataclass
class TransitModel:
    """
    Transit/shipping method assignment model. 
    Assigns transit mode based on size, density, and configuration.
    Uses weighted random choice to allow for variability.
    Returns transit mode, capacity, and cost.
    """
    pallet_base_weight: float
    container_base_weight: float
    courier_base_weight: float
    large_size_threshold: float
    medium_size_threshold: float
    small_size_threshold: float
    high_density_threshold: float
    large_container_multiplier: float
    large_pallet_multiplier: float
    large_courier_multiplier: float
    medium_container_multiplier: float
    medium_pallet_multiplier: float
    medium_courier_multiplier: float
    small_courier_multiplier: float
    small_pallet_multiplier: float
    small_container_multiplier: float
    default_pallet_multiplier: float
    default_container_multiplier: float
    courier_capacity: float
    courier_cost: float
    pallet_capacity: float
    pallet_cost: float
    container_capacity: float
    container_cost: float
    density_epsilon: float

    @staticmethod
    def _weighted_choice(pallet_weight: float, container_weight: float, courier_weight: float) -> Transits:
        """Select transit mode by weighted random choice."""
        pallet = max(0.0, pallet_weight)
        container = max(0.0, container_weight)
        courier = max(0.0, courier_weight)
        total = pallet + container + courier
        if total <= 0.0:
            return Transits.PALLET

        r = random.random() * total
        if r <= pallet:
            return Transits.PALLET
        if r <= pallet + container:
            return Transits.CONTAINER
        return Transits.COURIER

    def _mode_profile(self, transit: Transits) -> tuple[float, float]:
        if transit == Transits.COURIER:
            return self.courier_capacity, self.courier_cost
        if transit == Transits.CONTAINER:
            return self.container_capacity, self.container_cost
        return self.pallet_capacity, self.pallet_cost

    def assign_transit(self, price: float, size: float):
        """
        Assign transit mode and return (mode, capacity, cost).
        
        Applies rules based on size and density:
        - Large items favor container/pallet
        - Medium items have balanced weights
        - Small, high-density items favor courier"""
        density = price / max(self.density_epsilon, size)

        pallet_weight = self.pallet_base_weight
        container_weight = self.container_base_weight
        courier_weight = self.courier_base_weight

        if size >= self.large_size_threshold:
            container_weight *= self.large_container_multiplier
            pallet_weight *= self.large_pallet_multiplier
            courier_weight *= self.large_courier_multiplier
        elif size >= self.medium_size_threshold:
            container_weight *= self.medium_container_multiplier
            pallet_weight *= self.medium_pallet_multiplier
            courier_weight *= self.medium_courier_multiplier
        elif size <= self.small_size_threshold and density >= self.high_density_threshold:
            courier_weight *= self.small_courier_multiplier
            pallet_weight *= self.small_pallet_multiplier
            container_weight *= self.small_container_multiplier
        else:
            pallet_weight *= self.default_pallet_multiplier
            container_weight *= self.default_container_multiplier

        transit = self._weighted_choice(pallet_weight, container_weight, courier_weight)
        transit_capacity, transit_cost = self._mode_profile(transit)
        return transit, transit_capacity, transit_cost


@dataclass
class LogisticsModel:
    """Logistics difficulty model. Calculates difficulty based on size."""
    penalty_factor: float
    max_difficulty: float
    min_size_log: float
    optimal: float
    base_cost: float
    
    def calculate_logistics(self, size: float) -> float:
        """
        Calculate logistics difficulty (0.0 to 1.0).
        U-shaped curve: optimal at standard size, higher for very small/large.
        """
        log_size = math.log10(max(self.min_size_log, size))
        log_opt = math.log10(self.optimal)
        diff = log_size - log_opt
        penalty = self.penalty_factor * (diff ** 2)
        val = self.base_cost + penalty
        return min(self.max_difficulty, val)


@dataclass
class StockModel:
    """Stock/supply model. Calculates stock limits based on price and size."""
    base_stock: float
    min_stock: int
    noise: float
    infinite_stock_value: int
    infinite_chance_base: float
    infinite_decay_scale: float
    infinite_decay_size_multiplier: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    min_price_norm: float
    min_size_norm: float
    min_scale: float

    def generate_stock(self, price: float, size: float) -> int:
        """
        Generate stock/supply limit.
        Commodities (cheap/small) have high supply.
        Luxury/bulky items have limited supply.
        Small chance of effectively infinite stock.
        
        Assigns no stock limit to a percentage of items based on price and size, simulating commodities.
        
        Smooths stock limits with exponential decay based on price and size, with added noise for variability.
        """
        chance_infinite = self.infinite_chance_base
        chance_infinite *= math.exp(-price / self.infinite_decay_scale)
        chance_infinite *= math.exp(-size / (self.infinite_decay_scale * self.infinite_decay_size_multiplier))
        chance_infinite = max(0.0, min(1.0, chance_infinite))
        
        if random.random() < chance_infinite:
            return self.infinite_stock_value

        price_norm = (math.log10(max(self.min_price_norm, price)) / math.log10(max(self.min_scale, self.price_scale)))
        size_norm = (math.log10(max(self.min_size_norm, size)) / math.log10(max(self.min_scale, self.size_scale)))
        stock_penalty = (self.price_sensitivity * price_norm) + (self.size_sensitivity * size_norm)
        stock = self.base_stock * math.exp(-stock_penalty)
        stock *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_stock, int(stock))


def generate_zone_values(min_val: float, max_val: float, zones: List[Zone]) -> List[int]:
    """
    Generate discretized values across multiple zones.
    
    Returns list of integers representing price or size buckets.
    Handles span distribution, overlap prevention, and rounding.
    
    Each zone generates values in its assigned span, with density controlled by mode and bias.
    """
    gr = variables.guardrails
    total_span = max_val - min_val
    total_share = sum(z.span_share for z in zones)
    norm_shares = [z.span_share / total_share for z in zones]
    
    values = []
    boundary = min_val
    
    for idx, (zone, share) in enumerate(zip(zones, norm_shares)):
        zone_span = total_span * share
        zone_start = boundary
        zone_end = zone_start + zone_span
        
        zone_vals = zone.mode.generate(zone_start, zone_end, zone)
        
        rounded = [max(gr.round_min, int(round(v))) for v in zone_vals]
        
        if idx > 0:
            rounded = rounded[1:]
        
        values.extend(rounded)
        boundary = zone_end
    
    return values


class ProductGenerator:
    """
    Product catalog generator 
    
    Generates Cartesian product of price-size combinations with attributes calculated by models.
    
    Builds zones/models via cfg.
    """
    
    def __init__(self):
        """Initialize generator."""
        self.gen_cfg = variables.generation
        
        self.price_zones = self._build_zones(self.gen_cfg.price_zones)
        self.size_zones = self._build_zones(self.gen_cfg.size_zones)
        
        self.demand_model = self._build_demand_model()
        self.markup_model = self._build_markup_model()
        self.transit_model = self._build_transit_model()
        self.logistics_model = self._build_logistics_model()
        self.stock_model = self._build_stock_model()

    @staticmethod
    def _log(message: str):
        log("generator", message)
    
    def _build_zones(self, zone_configs: List) -> List[Zone]:
        """Convert zone configs to Zone objects with mode instances."""
        zones = []
        for zc in zone_configs:
            mode_name = zc.mode if hasattr(zc, 'mode') else 'power'
            mode_obj = MODE_REGISTRY.get(mode_name, PowerCurveMode())
            
            zones.append(Zone(
                mode=mode_obj,
                span_share=float(zc.span_share),
                resolution=zc.resolution,
                bias=zc.bias,
                step=zc.step
            ))
        return zones
    
    def _build_demand_model(self) -> DemandModel:
        """Build demand model from config."""
        cfg = variables.demand
        return DemandModel(
            base_demand=cfg.base_demand,
            price_scale=cfg.price_scale,
            size_scale=cfg.size_scale,
            price_sensitivity=cfg.price_sensitivity,
            size_sensitivity=cfg.size_sensitivity,
            noise=cfg.noise,
            min_demand=cfg.min_demand,
            max_demand=cfg.max_demand
        )
    
    def _build_markup_model(self) -> MarkupModel:
        """Build markup model from config."""
        cfg = variables.markup
        return MarkupModel(
            base_rate=cfg.base_rate,
            price_scale=cfg.price_scale,
            max_rate=cfg.max_rate,
            noise=cfg.noise,
            price_divisor=cfg.price_divisor,
            min_rate=cfg.min_rate,
            max_rate_clamp=cfg.max_rate_clamp
        )
    
    def _build_transit_model(self) -> TransitModel:
        """Build transit model from config."""
        cfg = variables.transit
        return TransitModel(
            pallet_base_weight=cfg.pallet_base_weight,
            container_base_weight=cfg.container_base_weight,
            courier_base_weight=cfg.courier_base_weight,
            large_size_threshold=cfg.large_size_threshold,
            medium_size_threshold=cfg.medium_size_threshold,
            small_size_threshold=cfg.small_size_threshold,
            high_density_threshold=cfg.high_density_threshold,
            large_container_multiplier=cfg.large_container_multiplier,
            large_pallet_multiplier=cfg.large_pallet_multiplier,
            large_courier_multiplier=cfg.large_courier_multiplier,
            medium_container_multiplier=cfg.medium_container_multiplier,
            medium_pallet_multiplier=cfg.medium_pallet_multiplier,
            medium_courier_multiplier=cfg.medium_courier_multiplier,
            small_courier_multiplier=cfg.small_courier_multiplier,
            small_pallet_multiplier=cfg.small_pallet_multiplier,
            small_container_multiplier=cfg.small_container_multiplier,
            default_pallet_multiplier=cfg.default_pallet_multiplier,
            default_container_multiplier=cfg.default_container_multiplier,
            courier_capacity=cfg.courier_capacity,
            courier_cost=cfg.courier_cost,
            pallet_capacity=cfg.pallet_capacity,
            pallet_cost=cfg.pallet_cost,
            container_capacity=cfg.container_capacity,
            container_cost=cfg.container_cost,
            density_epsilon=cfg.density_epsilon
        )
    
    def _build_logistics_model(self) -> LogisticsModel:
        """Build logistics model from config."""
        cfg = variables.logistics
        return LogisticsModel(
            penalty_factor=cfg.penalty_factor,
            max_difficulty=cfg.max_difficulty,
            min_size_log=cfg.min_size_log,
            optimal=self.gen_cfg.logistics_optimal,
            base_cost=self.gen_cfg.logistics_base_cost
        )
    
    def _build_stock_model(self) -> StockModel:
        """Build stock model from config."""
        cfg = variables.stock
        return StockModel(
            base_stock=cfg.base_stock,
            min_stock=cfg.min_stock,
            noise=cfg.noise,
            infinite_stock_value=cfg.infinite_stock_value,
            infinite_chance_base=cfg.infinite_chance_base,
            infinite_decay_scale=cfg.infinite_decay_scale,
            infinite_decay_size_multiplier=cfg.infinite_decay_size_multiplier,
            price_scale=cfg.price_scale,
            size_scale=cfg.size_scale,
            price_sensitivity=cfg.price_sensitivity,
            size_sensitivity=cfg.size_sensitivity,
            min_price_norm=cfg.min_price_norm,
            min_size_norm=cfg.min_size_norm,
            min_scale=cfg.min_scale
        )
    
    def generate(self) -> List[Product]:
        """
        Generate full Cartesian product of price-size combinations.
        
        Returns list of Product objects with all attributes calculated.
        
        Calculates attributes for each price-size combination using the respective models.
        """
        self._log("Starting product generation")
        prices = generate_zone_values(self.gen_cfg.min_price,self.gen_cfg.max_price,self.price_zones)
        sizes = generate_zone_values(self.gen_cfg.min_size,self.gen_cfg.max_size,self.size_zones)
        self._log(
            f"Built price buckets: total={format_number(len(prices))}, unique={format_number(len(set(prices)))}, "
            f"min={format_price(min(prices))}, max={format_price(max(prices))}"
        )
        self._log(
            f"Built size buckets: total={format_number(len(sizes))}, unique={format_number(len(set(sizes)))}, "
            f"min={format_volume(min(sizes))}, max={format_volume(max(sizes))}"
        )

        total_combinations = len(prices) * len(sizes)
        self._log(f"Cartesian combinations to evaluate: {format_number(total_combinations)}")

        products = []
        transit_counts = {Transits.COURIER: 0, Transits.PALLET: 0, Transits.CONTAINER: 0}
        infinite_stock_count = 0
        progress_step = max(1, total_combinations // 10)

        for idx, (price, size) in enumerate(itertools.product(prices, sizes), start=1):
            transit, transit_capacity, transit_cost = self.transit_model.assign_transit(price, size)
            demand = self.demand_model.evaluate(price, size)
            logistics = self.logistics_model.calculate_logistics(size)
            markup = self.markup_model.evaluate(price)
            stock = self.stock_model.generate_stock(price, size)

            transit_counts[transit] += 1
            if stock == self.stock_model.infinite_stock_value:
                infinite_stock_count += 1
            
            products.append(Product(
                id=f"P{idx:06d}",
                price=price,
                size=size,
                logistics=round(logistics, 3),
                transit=transit,
                transit_size=transit_capacity,
                transit_cost=transit_cost,
                demand=round(demand, 3),
                markup=round(markup, 3),
                stock=stock,
            ))

            if idx % progress_step == 0 or idx == total_combinations:
                pct = (idx / total_combinations) * 100.0
                self._log(f"Working through combinations: {format_number(idx)}/{format_number(total_combinations)} ({pct:.1f}%)")

        self._log(
            "Transit mix: "
            f"courier={format_number(transit_counts[Transits.COURIER])}, "
            f"pallet={format_number(transit_counts[Transits.PALLET])}, "
            f"container={format_number(transit_counts[Transits.CONTAINER])}"
        )
        self._log(f"Infinite-stock products: {format_number(infinite_stock_count)}")
        self._log(f"Generation complete. Total products: {format_number(len(products))}")
        
        return products


if __name__ == "__main__":
    generator = ProductGenerator()
    products = generator.generate()
    out_dir = os.path.join(PROJECT_ROOT, "data", "output")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    out_path = os.path.join(out_dir, f"{script_name}_{timestamp}.csv")
    ProductRepository.export_products(products, out_path)
    log("generator", f"Done. Generated {len(products)} products -> {out_path}")
