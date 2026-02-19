# "Cartesian Product Enumeration" 

from dataclasses import field
import itertools
import math
import os
import random
import time
import numpy as np
from typing import List, Protocol

from common import Transits, Product, dataclass, ProductRepository, load_config

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class SegmentMode(Protocol):
    def generate(self, start: float, end: float, seg: "Segment") -> List[float]:
        ...


@dataclass
class ExactMode:
    def generate(self, start: float, end: float, seg: "Segment") -> List[float]:
        span = max(0.0, end - start)
        step = max(1.0, seg.step)
        count = max(int(span / step) + 1, 1)
        values = np.linspace(start, end, count)
        return [float(v) for v in values]


@dataclass
class PowerCurveMode:
    def generate(self, start: float, end: float, seg: "Segment") -> List[float]:
        points = max(2, seg.points)
        t = np.linspace(0.0, 1.0, points)
        shaped = t ** max(0.01, seg.shape)
        values = start + (end - start) * shaped
        return [float(v) for v in values]


@dataclass
class GeometricMode:
    def generate(self, start: float, end: float, seg: "Segment") -> List[float]:
        points = max(2, seg.points)
        safe_start = max(1.0, start)
        safe_end = max(safe_start, end)
        ratio = (safe_end / safe_start) ** (1.0 / (points - 1))
        values = [safe_start * (ratio ** i) for i in range(points)]
        return values


@dataclass
class UShapeMode:
    def generate(self, start: float, end: float, seg: "Segment") -> List[float]:
        points = max(2, seg.points)
        t = np.linspace(0.0, 1.0, points)
        edge_dense = 0.5 - 0.5 * np.cos(np.pi * t)
        values = start + (end - start) * edge_dense
        return [float(v) for v in values]


@dataclass
class Segment:
    mode: SegmentMode = field(default_factory=PowerCurveMode)
    weight: float = 1.0
    points: int = 10
    shape: float = 1.0
    step: float = 1.0


@dataclass
class PriceModel:
    min_price: float
    max_price: float
    segments: List[Segment] = field(default_factory=lambda: [Segment()])

    def generate(self) -> List[int]:
        total_weight = sum(s.weight for s in self.segments)
        norm_weights = [s.weight / total_weight for s in self.segments]
        total_span = (self.max_price - self.min_price)
        prices: List[int] = []
        current = self.min_price
        for idx, (seg, w) in enumerate(zip(self.segments, norm_weights)):
            span = total_span * w
            start = current
            end = start + span
            seg_prices = seg.mode.generate(start, end, seg)
            rounded_segment = [max(1, int(round(v))) for v in seg_prices]
            if idx > 0:
                rounded_segment = rounded_segment[1:]
            prices.extend(rounded_segment)
            current = end
        return prices


@dataclass
class SizeModel:
    min_size: float
    max_size: float
    segments: List[Segment] = field(default_factory=lambda: [Segment()])
    
    def generate(self) -> List[int]:
        total_weight = sum(s.weight for s in self.segments)
        norm_weights = [s.weight / total_weight for s in self.segments]
        total_span = (self.max_size - self.min_size)
        sizes: List[int] = []
        current = self.min_size

        for idx, (seg, w) in enumerate(zip(self.segments, norm_weights)):
            span = total_span * w
            start = current
            end = start + span
            seg_sizes = seg.mode.generate(start, end, seg)
            rounded_segment = [max(1, int(round(v))) for v in seg_sizes]
            if idx > 0:
                rounded_segment = rounded_segment[1:]
            sizes.extend(rounded_segment)
            current = end
        return sizes


@dataclass
class DemandModel:
    base_demand: float = 0.9
    price_scale: float = 10000.0
    size_scale: float = 100000.0
    price_sensitivity: float = 1.8
    size_sensitivity: float = 1.2
    noise: float = 0.08
    min_demand: float = 0.03
    
    def evaluate(self, price: float, size: float) -> float:
        price_norm = math.log10(max(1.0, price)) / math.log10(max(10.0, self.price_scale))
        size_norm = math.log10(max(1.0, size)) / math.log10(max(10.0, self.size_scale))
        demand_penalty = (self.price_sensitivity * price_norm) + (self.size_sensitivity * size_norm)
        demand = self.base_demand * math.exp(-demand_penalty)
        demand *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_demand, min(0.99, demand))


@dataclass
class MarkupModel:
    base_rate: float = 0.05
    price_scale: float = 0.35
    max_rate: float = 0.6
    noise: float = 0.12
    
    def evaluate(self, price: float) -> float:
        price_factor = math.log10(max(1.0, price)) / 4.0
        rate = self.base_rate + (price_factor * self.price_scale)
        rate = min(self.max_rate, max(0.01, rate))
        rate *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(0.01, min(0.99, rate))


@dataclass
class TransitModel:
    pallet_base_weight: float = 0.60
    container_base_weight: float = 0.30
    courier_base_weight: float = 0.10

    @staticmethod
    def _weighted_choice(weights: dict[Transits, float]) -> Transits:
        total = sum(max(0.0, w) for w in weights.values())
        if total <= 0.0:
            return Transits.PALLET

        r = random.random() * total
        acc = 0.0
        for transit, weight in weights.items():
            acc += max(0.0, weight)
            if r <= acc:
                return transit
        return Transits.PALLET

    def assign_transit(self, price: float, size: float):
        density = price / max(0.001, size)
        weights = {
            Transits.PALLET: self.pallet_base_weight,
            Transits.CONTAINER: self.container_base_weight,
            Transits.COURIER: self.courier_base_weight,
        }

        if size >= 60000:
            weights[Transits.CONTAINER] *= 2.5
            weights[Transits.PALLET] *= 0.5
            weights[Transits.COURIER] *= 0.05
        elif size >= 8000:
            weights[Transits.CONTAINER] *= 1.3
            weights[Transits.PALLET] *= 1.1
            weights[Transits.COURIER] *= 0.2
        elif size <= 100 and density >= 10.0:
            weights[Transits.COURIER] *= 3.0
            weights[Transits.PALLET] *= 0.8
            weights[Transits.CONTAINER] *= 0.2
        else:
            weights[Transits.PALLET] *= 1.4
            weights[Transits.CONTAINER] *= 0.8

        transit = self._weighted_choice(weights)

        if transit == Transits.COURIER:
            transit_size, transit_cost = 50.0, 20.0
        elif transit == Transits.CONTAINER:
            transit_size, transit_cost = 50000.0, 1500.0
        elif transit == Transits.PALLET:
            transit_size, transit_cost = 5000.0, 400.0

        return transit, transit_size, transit_cost
    

@dataclass
class LogisticsModel:
    def calculate_logistics(self, size: float, optimal_mod: float, base_cost: float) -> float:
        """
        Logistics difficulty curve (0.0 to 1.0).
        - Optimal modifier:     Standard (optimal_mod)
        - Small items:          Easy to store/ship, but have higher handling.
        - Large items:          Special equipment / expensive storage.
        
        Implementation:
        - We look for a U-shaped curve.
        - Used a quadratic penalty based on the log-distance from the optimal size.
        """
        
        log_size = math.log10(max(1.0, size))
        log_opt = math.log10(optimal_mod)
        diff = log_size - log_opt
        penalty = 0.15 * (diff ** 2)
        val = base_cost + penalty
        return min(0.95, val)


@dataclass
class QuantityModel:
    base_quantity: float = 5000.0
    min_stock: int = 20
    noise: float = 0.1
    infinite_stock_value: int = 2_147_483_647
    infinite_chance_base: float = 0.08
    infinite_decay_scale: float = 4000.0
    price_scale: float = 10000.0
    size_scale: float = 100000.0
    price_sensitivity: float = 1.0
    size_sensitivity: float = 1.1

    def generate_stock(self, price: float, size: float) -> int:
        """
        Stock/Supply Limit.
        
        - Commodities (cheap, small):    High supply
        - Luxury items (expensive):      Scarce supply
        - Bulky items (large):           Limited by space
        
        Implementation:
        - Supply decays exponentially with price and size
        - Higher prices and larger items have lower stock
        - Optional chance of effectively infinite stock (encoded as large int)
        - Random noise for variance
        """
        chance_infinite = self.infinite_chance_base
        chance_infinite *= math.exp(-price / self.infinite_decay_scale)
        chance_infinite *= math.exp(-size / (self.infinite_decay_scale * 4.0))
        chance_infinite = max(0.0, min(1.0, chance_infinite))
        if random.random() < chance_infinite:
            return self.infinite_stock_value

        price_norm = math.log10(max(1.0, price)) / math.log10(max(10.0, self.price_scale))
        size_norm = math.log10(max(1.0, size)) / math.log10(max(10.0, self.size_scale))
        stock_penalty = (self.price_sensitivity * price_norm) + (self.size_sensitivity * size_norm)
        stock = self.base_quantity * math.exp(-stock_penalty)
        stock *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_stock, int(stock))


class ProductGenerator:
    """Encapsulates product generation with configurable models."""
    
    def __init__(
        self,
        price_range: tuple[float, float] = (1.0, 10000.0),
        size_range: tuple[float, float] = (0.1, 100000.0),
        logistics_optimal: float = 2000.0,
        logistics_base_cost: float = 0.5,
        price_segments: List[Segment] | None = None,
        size_segments: List[Segment] | None = None,
    ):
        """Initialize generator with model configurations."""
        configured_price_segments = (price_segments if price_segments is not None else self._default_price_segments(price_range))
        configured_size_segments = (
            size_segments if size_segments is not None else self._default_size_segments()
        )
        
        self.price_model = PriceModel(
            min_price=price_range[0],
            max_price=price_range[1],
            segments=configured_price_segments,
        )
        self.size_model = SizeModel(
            min_size=size_range[0],
            max_size=size_range[1],
            segments=configured_size_segments,
        )
        self.demand_model = DemandModel()
        self.markup_model = MarkupModel()
        self.transit_model = TransitModel()
        self.logistics_model = LogisticsModel()
        self.quantity_model = QuantityModel()
        self.logistics_optimal = logistics_optimal
        self.logistics_base_cost = logistics_base_cost

    @staticmethod
    def _default_price_segments(price_range: tuple[float, float]) -> List[Segment]:
        min_price, max_price = price_range
        breakpoint_price = 20.0
        total_span = max(1.0, max_price - min_price)
        first_span = max(0.0, min(breakpoint_price, max_price) - min_price)
        first_weight = max(0.0001, first_span / total_span)
        second_weight = max(0.0001, 1.0 - first_weight)

        return [
            Segment(weight=first_weight, mode=ExactMode(), step=1.0),
            Segment(weight=second_weight, points=81, mode=GeometricMode()),
        ]

    @staticmethod
    def _default_size_segments() -> List[Segment]:
        return [
            Segment(weight=0.30, points=41, mode=UShapeMode()),
            Segment(weight=0.40, points=20, mode=PowerCurveMode(), shape=1.0),
            Segment(weight=0.30, points=41, mode=UShapeMode()),
        ]
    
    def generate(self) -> List[Product]:
        """Generate full Cartesian product enumeration of all price-size bucket combinations."""
        prices = self.price_model.generate()
        sizes = self.size_model.generate()
        
        products = []
        
        for idx, (p, s) in enumerate(itertools.product(prices, sizes), start=1):
            transit, _, _ = self.transit_model.assign_transit(p, s)
            demand = self.demand_model.evaluate(p, s)
            logistics = self.logistics_model.calculate_logistics(s, self.logistics_optimal, self.logistics_base_cost)
            markup = self.markup_model.evaluate(p)
            stock = self.quantity_model.generate_stock(p, s)
            
            products.append(Product(
                id=f"P{idx:06d}",
                price=p,
                size=s,
                logistics=round(logistics, 3),
                transit=transit,
                demand=round(demand, 3),
                markup=round(markup, 3),
                stock=stock,
            ))
        
        return products


def generate_products() -> List[Product]:
    """Generate products using configuration wired to app.yaml."""
    config = load_config()
    
    # Defaults
    price_range = (1.0, 10000.0)
    size_range = (0.1, 100000.0)
    
    # Extract from app.yaml structure
    gen_config = config.get('generation', {})
    if 'price_range' in gen_config:
        pr = gen_config['price_range']
        if isinstance(pr, list) and len(pr) == 2:
            price_range = (float(pr[0]), float(pr[1]))
            
    if 'size_range' in gen_config:
        sr = gen_config['size_range']
        if isinstance(sr, list) and len(sr) == 2:
            size_range = (float(sr[0]), float(sr[1]))

    print(f"Generating products using wired config: Price={price_range}, Size={size_range}")
    
    generator = ProductGenerator(
        price_range=price_range,
        size_range=size_range
    )
    return generator.generate()


if __name__ == "__main__":
    products = generate_products()
    out_dir = os.path.join(PROJECT_ROOT, "data", "output")
    script_name = os.path.splitext(os.path.basename(__file__))[0]
    display_timestamp = time.strftime("%H:%M_%d/%m")
    timestamp = display_timestamp.replace(":", "-").replace("/", "-")
    out_path = os.path.join(out_dir, f"{script_name}_{timestamp}.csv")
    ProductRepository.export_products(products, out_path)
