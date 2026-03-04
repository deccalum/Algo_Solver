import algsolver_pb2


def build_dev_default() -> object:
    config = getattr(algsolver_pb2, "AppConfig")()

    config.generation.budget = 50000.0
    config.generation.space = 5.0e9
    config.generation.min_price = 1.0
    config.generation.max_price = 10000.0
    config.generation.min_size = 0.1
    config.generation.max_size = 100000.0
    config.generation.logistics_optimal = 2000.0
    config.generation.logistics_base_cost = 0.5

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
    size_zone.mode = "u_shape"
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
    size_zone.mode = "u_shape"
    size_zone.resolution = 352
    size_zone.step = 1.0
    size_zone.bias = 1.0

    config.generation.zone_defaults.span_share = 1.0
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

    config.transit.pallet_base_weight = 0.6
    config.transit.container_base_weight = 0.3
    config.transit.courier_base_weight = 0.1
    config.transit.large_size_threshold = 60000.0
    config.transit.medium_size_threshold = 8000.0
    config.transit.small_size_threshold = 100.0
    config.transit.high_density_threshold = 10.0
    config.transit.large_container_multiplier = 2.5
    config.transit.large_pallet_multiplier = 0.5
    config.transit.large_courier_multiplier = 0.05
    config.transit.medium_container_multiplier = 1.3
    config.transit.medium_pallet_multiplier = 1.1
    config.transit.medium_courier_multiplier = 0.2
    config.transit.small_courier_multiplier = 3.0
    config.transit.small_pallet_multiplier = 0.8
    config.transit.small_container_multiplier = 0.2
    config.transit.default_pallet_multiplier = 1.4
    config.transit.default_container_multiplier = 0.8
    config.transit.courier_capacity = 50.0
    config.transit.courier_cost = 20.0
    config.transit.pallet_capacity = 5000.0
    config.transit.pallet_cost = 400.0
    config.transit.container_capacity = 50000.0
    config.transit.container_cost = 1500.0
    config.transit.density_epsilon = 0.001

    config.logistics.penalty_factor = 0.15
    config.logistics.max_difficulty = 0.95
    config.logistics.min_size_log = 1.0

    config.stock.base_stock = 5000.0
    config.stock.min_stock = 20
    config.stock.noise = 0.1
    config.stock.infinite_stock_value = 2147483647
    config.stock.infinite_chance_base = 0.08
    config.stock.infinite_decay_scale = 4000.0
    config.stock.infinite_decay_size_multiplier = 4.0
    config.stock.price_scale = 10000.0
    config.stock.size_scale = 100000.0
    config.stock.price_sensitivity = 1.0
    config.stock.size_sensitivity = 1.1
    config.stock.min_price_norm = 1.0
    config.stock.min_size_norm = 1.0
    config.stock.min_scale = 10.0

    return config


dev_default = build_dev_default()
