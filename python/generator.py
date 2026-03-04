"""
Cartesian Product Enumeration
"""
import itertools
import math
import random
import numpy as np
from typing import List, Protocol
from dataclasses import dataclass

import algsolver_pb2
from common import format_number, format_price, format_volume, log


ProductItemMessage = getattr(algsolver_pb2, "ProductItem")


class ZoneMode(Protocol):
    """Protocol for zone value generation strategies."""

    def generate(
        self, start: float, end: float, zone: "Zone", guardrails
    ) -> List[float]: ...


@dataclass
class ExactMode:
    """Generate values at exact step intervals."""

    def generate(
        self, start: float, end: float, zone: "Zone", guardrails
    ) -> List[float]:
        span = max(guardrails.min_span, end - start)
        step = max(guardrails.min_step, zone.step)
        count = max(int(span / step) + 1, guardrails.min_count)
        values = np.linspace(start, end, count)
        return [float(v) for v in values]


@dataclass
class PowerCurveMode:
    """Generate values along a power curve (bias controls concentration)."""

    def generate(
        self, start: float, end: float, zone: "Zone", guardrails
    ) -> List[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        shaped = t ** max(guardrails.min_bias, zone.bias)
        values = start + (end - start) * shaped
        return [float(v) for v in values]


@dataclass
class GeometricMode:
    """Generate values in geometric progression."""

    def generate(
        self, start: float, end: float, zone: "Zone", guardrails
    ) -> List[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        if resolution <= 1:
            return [float(start)]

        safe_start = max(guardrails.min_safe_start, start)
        safe_end = max(safe_start, end)
        ratio = (safe_end / safe_start) ** (1.0 / (resolution - 1))
        return [safe_start * (ratio**i) for i in range(resolution)]


@dataclass
class UShapeMode:
    """Generate values with edge density (U-shaped distribution)."""

    def generate(
        self, start: float, end: float, zone: "Zone", guardrails
    ) -> List[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        edge_dense = 0.5 - 0.5 * np.cos(np.pi * t)
        values = start + (end - start) * edge_dense
        return [float(v) for v in values]


MODE_REGISTRY: dict[str, ZoneMode] = {
    "exact": ExactMode(),
    "power": PowerCurveMode(),
    "geometric": GeometricMode(),
    "u_shape": UShapeMode(),
}


@dataclass
class Zone:
    """Zone configuration used for value generation."""

    mode: ZoneMode
    span_share: float
    resolution: int
    bias: float
    step: float


@dataclass
class DemandModel:
    """Demand probability model."""

    base_demand: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    noise: float
    min_demand: float
    max_demand: float

    def evaluate(self, price: float, size: float) -> float:
        price_norm = math.log10(max(1.0, price)) / math.log10(
            max(10.0, self.price_scale)
        )
        size_norm = math.log10(max(1.0, size)) / math.log10(max(10.0, self.size_scale))
        demand_penalty = (self.price_sensitivity * price_norm) + (
            self.size_sensitivity * size_norm
        )
        demand = self.base_demand * math.exp(-demand_penalty)
        demand *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_demand, min(self.max_demand, demand))


@dataclass
class MarkupModel:
    """Markup model."""

    base_rate: float
    price_scale: float
    max_rate: float
    noise: float
    price_divisor: float
    min_rate: float
    max_rate_clamp: float

    def evaluate(self, price: float) -> float:
        price_factor = math.log10(max(1.0, price)) / self.price_divisor
        rate = self.base_rate + (price_factor * self.price_scale)
        rate = min(self.max_rate, max(self.min_rate, rate))
        rate *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_rate, min(self.max_rate_clamp, rate))


@dataclass
class TransitModel:
    """Transit mode assignment model."""

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
    def _weighted_choice(
        pallet_weight: float, container_weight: float, courier_weight: float
    ) -> str:
        normalized = {
            "PALLET": max(0.0, pallet_weight),
            "CONTAINER": max(0.0, container_weight),
            "COURIER": max(0.0, courier_weight),
        }
        total = sum(normalized.values())
        if total <= 0.0:
            return "PALLET"

        draw = random.random() * total
        running = 0.0
        for mode in ("PALLET", "CONTAINER", "COURIER"):
            running += normalized.get(mode, 0.0)
            if draw <= running:
                return mode
        return "COURIER"

    def _mode_profile(self, transit: str) -> tuple[float, float]:
        profiles = {
            "COURIER": (self.courier_capacity, self.courier_cost),
            "CONTAINER": (self.container_capacity, self.container_cost),
            "PALLET": (self.pallet_capacity, self.pallet_cost),
        }
        return profiles.get(transit, profiles["PALLET"])

    def assign_transit(self, price: float, size: float):
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
        elif (
            size <= self.small_size_threshold and density >= self.high_density_threshold
        ):
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
    """Logistics difficulty model."""

    min_size_log: float
    penalty_factor: float
    max_difficulty: float
    optimal: float
    base_cost: float

    def calculate_logistics(self, size: float) -> float:
        log_size = math.log10(max(self.min_size_log, size))
        log_opt = math.log10(max(self.min_size_log, self.optimal))
        diff = log_size - log_opt
        penalty = self.penalty_factor * (diff**2)
        val = self.base_cost + penalty
        return min(self.max_difficulty, val)


@dataclass
class TransitModel_V2:
    """Transit selection by minimum total shipment cost for product volume."""

    courier_capacity: float
    courier_cost: float
    pallet_capacity: float
    pallet_cost: float
    container_capacity: float
    container_cost: float
    min_capacity_epsilon: float

    def _total_cost(self, size: float, mode_capacity: float, mode_cost: float) -> float:
        safe_capacity = max(self.min_capacity_epsilon, mode_capacity)
        trips = math.ceil(size / safe_capacity)
        return trips * mode_cost

    def min_total_cost(self, size: float) -> float:
        return min(
            self._total_cost(size, self.courier_capacity, self.courier_cost),
            self._total_cost(size, self.pallet_capacity, self.pallet_cost),
            self._total_cost(size, self.container_capacity, self.container_cost),
        )


@dataclass
class StockModel:
    """Stock supply model."""

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
        chance_infinite = self.infinite_chance_base
        chance_infinite *= math.exp(-price / self.infinite_decay_scale)
        chance_infinite *= math.exp(
            -size / (self.infinite_decay_scale * self.infinite_decay_size_multiplier)
        )
        chance_infinite = max(0.0, min(1.0, chance_infinite))

        if random.random() < chance_infinite:
            return self.infinite_stock_value

        price_norm = math.log10(max(self.min_price_norm, price)) / math.log10(
            max(self.min_scale, self.price_scale)
        )
        size_norm = math.log10(max(self.min_size_norm, size)) / math.log10(
            max(self.min_scale, self.size_scale)
        )
        stock_penalty = (self.price_sensitivity * price_norm) + (
            self.size_sensitivity * size_norm
        )
        stock = self.base_stock * math.exp(-stock_penalty)
        stock *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_stock, int(stock))


def generate_zone_values(
    min_val: float, max_val: float, zones: List[Zone], guardrails
) -> List[int]:
    """Generate integer bucket values from zones."""

    total_span = max_val - min_val
    total_share = sum(zone.span_share for zone in zones)
    if total_share <= 0:
        raise ValueError("Zone span_share total must be > 0")

    norm_shares = [zone.span_share / total_share for zone in zones]
    values: list[int] = []
    boundary = min_val

    for index, (zone, share) in enumerate(zip(zones, norm_shares)):
        zone_span = total_span * share
        zone_start = boundary
        zone_end = zone_start + zone_span

        zone_values = zone.mode.generate(zone_start, zone_end, zone, guardrails)
        rounded = [max(guardrails.round_min, int(round(v))) for v in zone_values]

        if index > 0:
            rounded = rounded[1:]

        values.extend(rounded)
        boundary = zone_end

    return values


class ProductGenerator:
    """Generate product catalog from protobuf `AppConfig`."""

    def __init__(self, app_config, use_transit_v2: bool = False):
        self.generation = app_config.generation
        self.guardrails = app_config.guardrails
        self.use_transit_v2 = use_transit_v2

        self.price_zones = self._build_zones(self.generation.price_zones)
        self.size_zones = self._build_zones(self.generation.size_zones)

        demand = app_config.demand
        self.demand_model = DemandModel(
            base_demand=demand.base_demand,
            price_scale=demand.price_scale,
            size_scale=demand.size_scale,
            price_sensitivity=demand.price_sensitivity,
            size_sensitivity=demand.size_sensitivity,
            noise=demand.noise,
            min_demand=demand.min_demand,
            max_demand=demand.max_demand,
        )

        markup = app_config.markup
        self.markup_model = MarkupModel(
            base_rate=markup.base_rate,
            price_scale=markup.price_scale,
            max_rate=markup.max_rate,
            noise=markup.noise,
            price_divisor=markup.price_divisor,
            min_rate=markup.min_rate,
            max_rate_clamp=markup.max_rate_clamp,
        )

        transit = app_config.transit
        self.transit_model = TransitModel(
            pallet_base_weight=transit.pallet_base_weight,
            container_base_weight=transit.container_base_weight,
            courier_base_weight=transit.courier_base_weight,
            large_size_threshold=transit.large_size_threshold,
            medium_size_threshold=transit.medium_size_threshold,
            small_size_threshold=transit.small_size_threshold,
            high_density_threshold=transit.high_density_threshold,
            large_container_multiplier=transit.large_container_multiplier,
            large_pallet_multiplier=transit.large_pallet_multiplier,
            large_courier_multiplier=transit.large_courier_multiplier,
            medium_container_multiplier=transit.medium_container_multiplier,
            medium_pallet_multiplier=transit.medium_pallet_multiplier,
            medium_courier_multiplier=transit.medium_courier_multiplier,
            small_courier_multiplier=transit.small_courier_multiplier,
            small_pallet_multiplier=transit.small_pallet_multiplier,
            small_container_multiplier=transit.small_container_multiplier,
            default_pallet_multiplier=transit.default_pallet_multiplier,
            default_container_multiplier=transit.default_container_multiplier,
            courier_capacity=transit.courier_capacity,
            courier_cost=transit.courier_cost,
            pallet_capacity=transit.pallet_capacity,
            pallet_cost=transit.pallet_cost,
            container_capacity=transit.container_capacity,
            container_cost=transit.container_cost,
            density_epsilon=transit.density_epsilon,
        )
        self.transit_model_v2 = TransitModel_V2(
            courier_capacity=transit.courier_capacity,
            courier_cost=transit.courier_cost,
            pallet_capacity=transit.pallet_capacity,
            pallet_cost=transit.pallet_cost,
            container_capacity=transit.container_capacity,
            container_cost=transit.container_cost,
            min_capacity_epsilon=transit.density_epsilon,
        )

        logistics = app_config.logistics
        self.logistics_model = LogisticsModel(
            min_size_log=logistics.min_size_log,
            penalty_factor=logistics.penalty_factor,
            max_difficulty=logistics.max_difficulty,
            optimal=self.generation.logistics_optimal,
            base_cost=self.generation.logistics_base_cost,
        )

        stock = app_config.stock
        self.stock_model = StockModel(
            base_stock=stock.base_stock,
            min_stock=stock.min_stock,
            noise=stock.noise,
            infinite_stock_value=stock.infinite_stock_value,
            infinite_chance_base=stock.infinite_chance_base,
            infinite_decay_scale=stock.infinite_decay_scale,
            infinite_decay_size_multiplier=stock.infinite_decay_size_multiplier,
            price_scale=stock.price_scale,
            size_scale=stock.size_scale,
            price_sensitivity=stock.price_sensitivity,
            size_sensitivity=stock.size_sensitivity,
            min_price_norm=stock.min_price_norm,
            min_size_norm=stock.min_size_norm,
            min_scale=stock.min_scale,
        )

    @classmethod
    def from_proto_config(
        cls, proto_app_config, use_transit_v2: bool = False
    ) -> "ProductGenerator":
        """Factory from protobuf `AppConfig` message."""

        return cls(proto_app_config, use_transit_v2=use_transit_v2)

    @staticmethod
    def _log(message: str):
        log("generator", message)

    def _build_zones(self, zone_configs) -> List[Zone]:
        zones: list[Zone] = []
        for zone_config in zone_configs:
            mode_obj = MODE_REGISTRY.get(zone_config.mode, MODE_REGISTRY["power"])
            zones.append(
                Zone(
                    mode=mode_obj,
                    span_share=float(zone_config.span_share),
                    resolution=int(zone_config.resolution),
                    bias=float(zone_config.bias),
                    step=float(zone_config.step),
                )
            )
        return zones

    def generate(self) -> List[object]:
        """Generate full Cartesian product of price-size combinations."""

        self._log("Starting product generation")

        prices = generate_zone_values(
            self.generation.min_price,
            self.generation.max_price,
            self.price_zones,
            self.guardrails,
        )
        sizes = generate_zone_values(
            self.generation.min_size,
            self.generation.max_size,
            self.size_zones,
            self.guardrails,
        )

        self._log(
            f"Built price buckets: total={format_number(len(prices))}, unique={format_number(len(set(prices)))}, "
            f"min={format_price(min(prices))}, max={format_price(max(prices))}"
        )
        self._log(
            f"Built size buckets: total={format_number(len(sizes))}, unique={format_number(len(set(sizes)))}, "
            f"min={format_volume(min(sizes))}, max={format_volume(max(sizes))}"
        )

        total_combinations = len(prices) * len(sizes)
        self._log(
            f"Cartesian combinations to evaluate: {format_number(total_combinations)}"
        )

        products: list[object] = []
        transit_counts = {"COURIER": 0, "PALLET": 0, "CONTAINER": 0}
        infinite_stock_count = 0
        progress_step = max(1, total_combinations // 10)

        for index, (price, size) in enumerate(
            itertools.product(prices, sizes), start=1
        ):
            transit_rule, transit_capacity_rule, transit_cost_rule = (
                self.transit_model.assign_transit(price, size)
            )
            transit_cost_v2 = self.transit_model_v2.min_total_cost(size)

            if self.use_transit_v2:
                transit, transit_capacity, transit_cost = (
                    transit_rule,
                    transit_capacity_rule,
                    transit_cost_v2,
                )
            else:
                transit, transit_capacity, transit_cost = (
                    transit_rule,
                    transit_capacity_rule,
                    transit_cost_rule,
                )

            demand = self.demand_model.evaluate(price, size)
            logistics_cost = self.logistics_model.calculate_logistics(size)
            markup = self.markup_model.evaluate(price)
            stock = self.stock_model.generate_stock(price, size)

            transit_counts[transit] += 1
            if stock == self.stock_model.infinite_stock_value:
                infinite_stock_count += 1

            products.append(
                ProductItemMessage(
                    id=f"P{index:06d}",
                    price=price,
                    size=size,
                    logistics=round(logistics_cost, 3),
                    transit=transit,
                    transit_size=transit_capacity,
                    transit_cost=transit_cost,
                    demand=round(demand, 3),
                    markup=round(markup, 3),
                    stock=stock,
                )
            )

            if index % progress_step == 0 or index == total_combinations:
                pct = (index / total_combinations) * 100.0
                self._log(
                    f"Working through combinations: {format_number(index)}/{format_number(total_combinations)} ({pct:.1f}%)"
                )

        self._log(
            "Transit mix: "
            f"courier={format_number(transit_counts['COURIER'])}, "
            f"pallet={format_number(transit_counts['PALLET'])}, "
            f"container={format_number(transit_counts['CONTAINER'])}"
        )
        self._log(
            f"Transit output model: {'V2_MIN_TOTAL_COST' if self.use_transit_v2 else 'V1_RULE_WEIGHTED'}"
        )
        self._log(f"Infinite-stock products: {format_number(infinite_stock_count)}")
        self._log(
            f"Generation complete. Total products: {format_number(len(products))}"
        )
        return products
