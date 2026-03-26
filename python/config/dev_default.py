import proto.algsolver_pb2 as algsolver_pb2
from typing import Any


def build_dev_default() -> Any:
    config = getattr(algsolver_pb2, "AppConfig")()

    config.generation.budget = 50000.0
    config.generation.space = 5.0e9
    config.generation.min_price = 1.0
    config.generation.max_price = 10000.0
    config.generation.min_size = 0.1
    config.generation.max_size = 100000.0

    price_zone = config.generation.price_zones.add()
    price_zone.span_share = 0.0
    price_zone.mode = "exact"
    price_zone.step = 1.0
    price_zone.resolution = 10
    price_zone.bias = 1.0

    price_zone = config.generation.price_zones.add()
    price_zone.span_share = 0.0
    price_zone.mode = "exact"
    price_zone.step = 2.0
    price_zone.resolution = 10
    price_zone.bias = 1.0

    price_zone = config.generation.price_zones.add()
    price_zone.span_share = 0.015
    price_zone.mode = "exact"
    price_zone.step = 5.0
    price_zone.resolution = 10
    price_zone.bias = 1.0

    price_zone = config.generation.price_zones.add()
    price_zone.span_share = 0.080
    price_zone.mode = "geometric"
    price_zone.step = 1.0
    price_zone.resolution = 24
    price_zone.bias = 1.0

    price_zone = config.generation.price_zones.add()
    price_zone.span_share = 0.905
    price_zone.mode = "geometric"
    price_zone.step = 1.0
    price_zone.resolution = 30
    price_zone.bias = 1.0

    size_zone = config.generation.size_zones.add()
    size_zone.span_share = 0.3
    size_zone.mode = "gaussian"
    size_zone.resolution = 352
    size_zone.step = 1.0
    size_zone.bias = 1.0

    size_zone = config.generation.size_zones.add()
    size_zone.span_share = 0.4
    size_zone.mode = "power"
    size_zone.resolution = 172
    size_zone.step = 1.0
    size_zone.bias = 1.0

    size_zone = config.generation.size_zones.add()
    size_zone.span_share = 0.3
    size_zone.mode = "gaussian"
    size_zone.resolution = 352
    size_zone.step = 1.0
    size_zone.bias = 1.0

    config.generation.zone_defaults.span_share = 1.0
    config.generation.zone_defaults.mode = "power"
    config.generation.zone_defaults.resolution = 10
    config.generation.zone_defaults.bias = 1.0
    config.generation.zone_defaults.step = 1.0

    config.guardrails.min_span = 0.0
    config.guardrails.min_step = 1.0
    config.guardrails.min_resolution = 2
    config.guardrails.min_bias = 0.01
    config.guardrails.min_safe_start = 1.0
    config.guardrails.min_count = 1
    config.guardrails.round_min = 1

    config.demand.base_demand = 0.9
    config.demand.price_scale = 10000.0
    config.demand.size_scale = 100000.0
    config.demand.price_sensitivity = 1.8
    config.demand.size_sensitivity = 1.2
    config.demand.noise = 0.08
    config.demand.min_demand = 0.03
    config.demand.max_demand = 0.99

    config.markup.base_rate = 0.05
    config.markup.price_scale = 0.35
    config.markup.max_rate = 0.6
    config.markup.noise = 0.12
    config.markup.price_divisor = 4.0
    config.markup.min_rate = 0.01
    config.markup.max_rate_clamp = 0.99

    config.logistics.optimal = 2000.0
    config.logistics.base_cost = 0.5
    config.logistics.penalty_factor = 0.15
    config.logistics.max_difficulty = 0.95
    config.logistics.min_size_log = 1.0

    config.transit.courier.name = "COURIER"
    config.transit.courier.capacity = 50.0
    config.transit.courier.base_cost = 45.0
    config.transit.courier.max_value_density = 1000.0
    config.transit.courier.min_weight_class = 0.0

    config.transit.pallet.name = "PALLET"
    config.transit.pallet.capacity = 5000.0
    config.transit.pallet.base_cost = 750.0
    config.transit.pallet.max_value_density = 250.0
    config.transit.pallet.min_weight_class = 50.0

    config.transit.container.name = "CONTAINER"
    config.transit.container.capacity = 50000.0
    config.transit.container.base_cost = 3500.0
    config.transit.container.max_value_density = 80.0
    config.transit.container.min_weight_class = 500.0

    config.transit.min_capacity_epsilon = 1e-6
    config.transit.weight_volume_ratio = 0.25
    config.transit.origin = 1.3
    config.transit.origin_zone.mode = "power"
    config.transit.origin_zone.span_share = 1.0
    config.transit.origin_zone.resolution = 8
    config.transit.origin_zone.step = 1.0
    config.transit.origin_zone.bias = 1.0

    config.stock.base_stock = 5000.0
    config.stock.min_stock = 20
    config.stock.noise = 0.1
    config.stock.infinite_stock_value = 2147483647
    config.stock.infinite_chance_base = 0.08
    config.stock.infinite_decay_scale = 4000.0
    config.stock.infinite_decay_size = 4.0
    config.stock.price_scale = 10000.0
    config.stock.size_scale = 100000.0
    config.stock.price_sensitivity = 1.0
    config.stock.size_sensitivity = 1.1
    config.stock.min_price_norm = 1.0
    config.stock.min_size_norm = 1.0
    config.stock.min_scale = 10.0

    return config


def build_dev_config() -> Any:
    return build_dev_default()


dev_default = build_dev_default()
