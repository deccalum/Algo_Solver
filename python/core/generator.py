from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Any, Protocol

import python.proto.algsolver_pb2 as algsolver_pb2
from mapper import from_proto
from python.core.zone import MODE_REGISTRY, Zones
from python.models.demand_model         import DemandModel
from python.models.logistics_model      import LogisticsModel
from python.models.markup_model         import MarkupModel
from python.models.stock_model          import StockModel
from python.models.transit_model        import TransitModel, TransitResult
from python.common import format_number, format_price, format_volume, log

class Guardrails(Protocol):
    min_span: float
    min_step: float
    min_resolution: int
    min_bias: float
    min_safe_start: float
    min_count: int
    round_min: int


class ZoneSpec(Protocol):
    mode: str
    span_share: float
    resolution: int
    bias: float
    step: float


class Generation(Protocol):
    min_price: float
    max_price: float
    min_size: float
    max_size: float
    price_zones: Iterable[ZoneSpec]
    size_zones: Iterable[ZoneSpec]


class AppConfig(Protocol):
    generation: Generation
    guardrails: Guardrails
    demand: Any
    markup: Any
    stock: Any
    transit: Any
    logistics: Any

Product = getattr(algsolver_pb2, "Product")

def generate_zone_values(
    min_val: float, max_val: float, zones: list[Zones], guardrails: Guardrails
) -> list[int]:
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

    generation:         Generation
    guardrails:         Guardrails
    price_zones:        list[Zones]
    size_zones:         list[Zones]
    demand_model:       DemandModel
    markup_model:       MarkupModel
    transit_model:      TransitModel
    logistics_model:    LogisticsModel
    stock_model:        StockModel

    def __init__(self, app_config: AppConfig) -> None:
        self.generation       = app_config.generation
        self.guardrails       = app_config.guardrails

        self.price_zones      = self._build_zones(self.generation.price_zones)
        self.size_zones       = self._build_zones(self.generation.size_zones)

        self.demand_model     = from_proto(DemandModel,     app_config.demand)
        self.markup_model     = from_proto(MarkupModel,     app_config.markup)
        self.stock_model      = from_proto(StockModel,      app_config.stock)
        self.transit_model    = from_proto(TransitModel,    app_config.transit)
        self.logistics_model  = from_proto(LogisticsModel,  app_config.logistics)

    @staticmethod
    def _log(message: str) -> None:
        log("generator", message)

    def _build_zones(self, zones: Iterable[Any]) -> list[Zones]:
        return [
            Zones(
                mode       = MODE_REGISTRY.get(zc.mode, MODE_REGISTRY["power"]),
                span_share = float(zc.span_share),
                resolution = int(zc.resolution),
                bias       = float(zc.bias),
                step       = float(zc.step),
            )
            for zc in zones
        ]

    @classmethod
    def from_proto_config(cls, proto_app_config: AppConfig) -> ProductGenerator:
        return cls(proto_app_config)

    def generate(self) -> list[Any]:
        self._log("Starting product generation")
        prices, sizes = self._build_value_ranges()
        products, stats = self._evaluate_all(prices, sizes)
        self._log_summary(products, stats)
        return products

    def _build_value_ranges(self) -> tuple[list[int], list[int]]:
        prices = generate_zone_values(
            self.generation.min_price, self.generation.max_price,
            self.price_zones, self.guardrails,
        )
        sizes = generate_zone_values(
            self.generation.min_size, self.generation.max_size,
            self.size_zones, self.guardrails,
        )
        self._log(f"Price buckets: total={format_number(len(prices))}, unique={format_number(len(set(prices)))}, "
                  f"min={format_price(min(prices))}, max={format_price(max(prices))}")
        self._log(f"Size buckets:  total={format_number(len(sizes))}, unique={format_number(len(set(sizes)))}, "
                  f"min={format_volume(min(sizes))}, max={format_volume(max(sizes))}")
        return prices, sizes

    def _evaluate_all(self, prices: list[int], sizes: list[int]) -> tuple[list[Any], dict[str, int]]:
        total = len(prices) * len(sizes)
        progress_step = max(1, total // 10)
        stats = {"COURIER": 0, "PALLET": 0, "CONTAINER": 0, "infinite_stock": 0}

        self._log(f"Cartesian combinations to evaluate: {format_number(total)}")

        products: list[Any] = []
        for index, (price, size) in enumerate(itertools.product(prices, sizes), start=1):
            product = self._evaluate_product(index, price, size)
            products.append(product)

            stats[product.transit] += 1
            if product.stock == self.stock_model.infinite_stock_value:
                stats["infinite_stock"] += 1

            if index % progress_step == 0 or index == total:
                self._log(f"Progress: {format_number(index)}/{format_number(total)} ({index / total * 100:.1f}%)")

        return products, stats
    
    def _resolve_transit(self, size: float, price: float, origin: float) -> TransitResult:
        return self.transit_model.assign_transit(size, price, origin)

    def _evaluate_product(self, index: int, price: float, size: float) -> Any:
        transit = self._resolve_transit(size, price, self.transit_model.origin)

        return Product(
            id           = f"P{index:06d}",
            price        = price,
            size         = size,
            demand       = round(self.demand_model.evaluate(price, size), 3),
            markup       = round(self.markup_model.evaluate(price), 3),
            logistics    = round(self.logistics_model.calculate_logistics(size), 3),
            stock        = self.stock_model.generate_stock(price, size),
            transit      = transit.mode,
            transit_size = transit.capacity,
            transit_cost = transit.cost,
        )
    def _log_summary(self, products: list[Any], stats: dict[str, int]) -> None:
        self._log(f"Transit mix: courier={format_number(stats['COURIER'])}, "
                  f"pallet={format_number(stats['PALLET'])}, "
                  f"container={format_number(stats['CONTAINER'])}")
        self._log(f"Infinite-stock products: {format_number(stats['infinite_stock'])}")
        self._log(f"Generation complete. Total products: {format_number(len(products))}")

if __name__ == "__main__":
    raise SystemExit("This module does not support direct execution in current state.\nUse other versions...")