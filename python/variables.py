"""
Config adapter - converts app.yaml into typed configuration objects for generator.
All generation parameters are loaded here, making generator.py clean and testable.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
import common


_cfg = common.load_config()


def _require_dict(value: Any, name: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid config section: {name}")
    return value


def _require_value(section: Dict[str, Any], key: str, section_name: str) -> Any:
    value = section.get(key)
    if value is None:
        raise ValueError(f"Missing required config key: {section_name}.{key}")
    return value


def _pick_zone_value(zone_dict: Dict[str, Any], defaults: Dict[str, Any], key: str) -> Any:
    value = zone_dict.get(key)
    if value is not None:
        return value
    default_value = defaults.get(key)
    if default_value is None:
        raise ValueError(f"Missing required zone key: {key}")
    return default_value


_gen = _require_dict(_cfg.get('generation'), 'generation')
_demand_cfg = _require_dict(_cfg.get('demand'), 'demand')
_markup_cfg = _require_dict(_cfg.get('markup'), 'markup')
_transit_cfg = _require_dict(_cfg.get('transit'), 'transit')
_logistics_cfg = _require_dict(_cfg.get('logistics'), 'logistics')
_stock_cfg = _require_dict(_cfg.get('stock'), 'stock')


@dataclass
class ZoneConfig:
    mode: str
    span_share: float
    resolution: int
    bias: float
    step: float


@dataclass
class GenerationConfig:
    min_price: float
    max_price: float
    min_size: float
    max_size: float
    logistics_optimal: float
    logistics_base_cost: float
    price_zones: List[ZoneConfig]
    size_zones: List[ZoneConfig]
    zone_defaults: Dict[str, Any]


@dataclass
class DemandConfig:
    base_demand: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    noise: float
    min_demand: float
    max_demand: float


@dataclass
class MarkupConfig:
    base_rate: float
    price_scale: float
    max_rate: float
    noise: float
    price_divisor: float
    min_rate: float
    max_rate_clamp: float


@dataclass
class TransitConfig:
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


@dataclass
class LogisticsConfig:
    penalty_factor: float
    max_difficulty: float
    min_size_log: float


@dataclass
class StockConfig:
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


@dataclass
class GuardrailsConfig:
    """Numeric guardrails for zone generation."""
    min_span: float
    min_step: float
    min_resolution: int
    min_bias: float
    min_safe_start: float
    min_count: int
    round_min: int


def _build_zone_config(zone_dict: Dict[str, Any], defaults: Dict[str, Any]) -> ZoneConfig:
    """Build a ZoneConfig from YAML dict, applying defaults."""
    mode = _pick_zone_value(zone_dict, defaults, 'mode')
    span_share = _pick_zone_value(zone_dict, defaults, 'span_share')
    resolution = _pick_zone_value(zone_dict, defaults, 'resolution')
    bias = _pick_zone_value(zone_dict, defaults, 'bias')
    step = _pick_zone_value(zone_dict, defaults, 'step')
    
    return ZoneConfig(
        mode=str(mode),
        span_share=float(span_share),
        resolution=int(resolution),
        bias=float(bias),
        step=float(step)
    )


def _load_generation_config() -> GenerationConfig:
    """Load and validate generation configuration."""
    price_range = _require_value(_gen, 'price_range', 'generation')
    size_range = _require_value(_gen, 'size_range', 'generation')
    zone_defaults = _require_dict(_require_value(_gen, 'zone_defaults', 'generation'), 'generation.zone_defaults')
    price_zones_raw = _require_value(_gen, 'price_zones', 'generation')
    price_zones_resolved = _resolve_auto_spans(price_zones_raw)
    price_zones = [_build_zone_config(z, zone_defaults) for z in price_zones_resolved]
    size_zones_raw = _require_value(_gen, 'size_zones', 'generation')
    size_zones_resolved = _resolve_auto_spans(size_zones_raw)
    size_zones = [_build_zone_config(z, zone_defaults) for z in size_zones_resolved]
    
    return GenerationConfig(
        min_price=float(price_range[0]),
        max_price=float(price_range[1]),
        min_size=float(size_range[0]),
        max_size=float(size_range[1]),
        logistics_optimal=float(_require_value(_gen, 'logistics_optimal', 'generation')),
        logistics_base_cost=float(_require_value(_gen, 'logistics_base_cost', 'generation')),
        price_zones=price_zones,
        size_zones=size_zones,
        zone_defaults=zone_defaults
    )


def _resolve_auto_spans(zones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolve 'auto' span_share values to calculated floats."""
    auto_count = 0
    fixed_total = 0.0
    
    for zone in zones:
        share = zone.get('span_share')
        if isinstance(share, str) and share.lower() == 'auto':
            auto_count += 1
        else:
            if share is None:
                raise ValueError("Missing required zone key: span_share")
            fixed_total += float(share)
    
    if auto_count > 0:
        remaining = max(0.0, 1.0 - fixed_total)
        auto_value = remaining / auto_count
    else:
        auto_value = 0.0
    
    resolved = []
    for zone in zones:
        zone_copy = zone.copy()
        share = zone.get('span_share')
        if isinstance(share, str) and share.lower() == 'auto':
            zone_copy['span_share'] = auto_value
        resolved.append(zone_copy)
    
    return resolved


def _load_demand_config() -> DemandConfig:
    """Load demand model configuration."""
    return DemandConfig(
        base_demand=float(_require_value(_demand_cfg, 'base_demand', 'demand')),
        price_scale=float(_require_value(_demand_cfg, 'price_scale', 'demand')),
        size_scale=float(_require_value(_demand_cfg, 'size_scale', 'demand')),
        price_sensitivity=float(_require_value(_demand_cfg, 'price_sensitivity', 'demand')),
        size_sensitivity=float(_require_value(_demand_cfg, 'size_sensitivity', 'demand')),
        noise=float(_require_value(_demand_cfg, 'noise', 'demand')),
        min_demand=float(_require_value(_demand_cfg, 'min_demand', 'demand')),
        max_demand=float(_require_value(_demand_cfg, 'max_demand', 'demand'))
    )


def _load_markup_config() -> MarkupConfig:
    """Load markup model configuration."""
    return MarkupConfig(
        base_rate=float(_require_value(_markup_cfg, 'base_rate', 'markup')),
        price_scale=float(_require_value(_markup_cfg, 'price_scale', 'markup')),
        max_rate=float(_require_value(_markup_cfg, 'max_rate', 'markup')),
        noise=float(_require_value(_markup_cfg, 'noise', 'markup')),
        price_divisor=float(_require_value(_markup_cfg, 'price_divisor', 'markup')),
        min_rate=float(_require_value(_markup_cfg, 'min_rate', 'markup')),
        max_rate_clamp=float(_require_value(_markup_cfg, 'max_rate_clamp', 'markup'))
    )


def _load_transit_config() -> TransitConfig:
    """Load transit model configuration."""
    raw_base_weights = _require_dict(_require_value(_transit_cfg, 'base_weights', 'transit'), 'transit.base_weights')
    raw_thresholds = _require_dict(_require_value(_transit_cfg, 'thresholds', 'transit'), 'transit.thresholds')
    raw_multipliers = _require_dict(_require_value(_transit_cfg, 'multipliers', 'transit'), 'transit.multipliers')
    raw_modes = _require_dict(_require_value(_transit_cfg, 'modes', 'transit'), 'transit.modes')

    return TransitConfig(
        pallet_base_weight=float(raw_base_weights['pallet']),
        container_base_weight=float(raw_base_weights['container']),
        courier_base_weight=float(raw_base_weights['courier']),
        large_size_threshold=float(raw_thresholds['large_size']),
        medium_size_threshold=float(raw_thresholds['medium_size']),
        small_size_threshold=float(raw_thresholds['small_size']),
        high_density_threshold=float(raw_thresholds['high_density']),
        large_container_multiplier=float(raw_multipliers['large_container']),
        large_pallet_multiplier=float(raw_multipliers['large_pallet']),
        large_courier_multiplier=float(raw_multipliers['large_courier']),
        medium_container_multiplier=float(raw_multipliers['medium_container']),
        medium_pallet_multiplier=float(raw_multipliers['medium_pallet']),
        medium_courier_multiplier=float(raw_multipliers['medium_courier']),
        small_courier_multiplier=float(raw_multipliers['small_courier']),
        small_pallet_multiplier=float(raw_multipliers['small_pallet']),
        small_container_multiplier=float(raw_multipliers['small_container']),
        default_pallet_multiplier=float(raw_multipliers['default_pallet']),
        default_container_multiplier=float(raw_multipliers['default_container']),
        courier_capacity=float(raw_modes['COURIER']['capacity']),
        courier_cost=float(raw_modes['COURIER']['cost']),
        pallet_capacity=float(raw_modes['PALLET']['capacity']),
        pallet_cost=float(raw_modes['PALLET']['cost']),
        container_capacity=float(raw_modes['CONTAINER']['capacity']),
        container_cost=float(raw_modes['CONTAINER']['cost']),
        density_epsilon=float(_require_value(_transit_cfg, 'density_epsilon', 'transit'))
    )


def _load_logistics_config() -> LogisticsConfig:
    """Load logistics model configuration."""
    return LogisticsConfig(
        penalty_factor=float(_require_value(_logistics_cfg, 'penalty_factor', 'logistics')),
        max_difficulty=float(_require_value(_logistics_cfg, 'max_difficulty', 'logistics')),
        min_size_log=float(_require_value(_logistics_cfg, 'min_size_log', 'logistics'))
    )


def _load_guardrails_config() -> GuardrailsConfig:
    """Load guardrails configuration."""
    gr = _require_dict(_require_value(_gen, 'guardrails', 'generation'), 'generation.guardrails')
    return GuardrailsConfig(
        min_span=float(_require_value(gr, 'min_span', 'generation.guardrails')),
        min_step=float(_require_value(gr, 'min_step', 'generation.guardrails')),
        min_resolution=int(_require_value(gr, 'min_resolution', 'generation.guardrails')),
        min_bias=float(_require_value(gr, 'min_bias', 'generation.guardrails')),
        min_safe_start=float(_require_value(gr, 'min_safe_start', 'generation.guardrails')),
        min_count=int(_require_value(gr, 'min_count', 'generation.guardrails')),
        round_min=int(_require_value(gr, 'round_min', 'generation.guardrails'))
    )


def _load_stock_config() -> StockConfig:
    """Load stock model configuration."""
    return StockConfig(
        base_stock=float(_require_value(_stock_cfg, 'base_stock', 'stock')),
        min_stock=int(_require_value(_stock_cfg, 'min_stock', 'stock')),
        noise=float(_require_value(_stock_cfg, 'noise', 'stock')),
        infinite_stock_value=int(_require_value(_stock_cfg, 'infinite_stock_value', 'stock')),
        infinite_chance_base=float(_require_value(_stock_cfg, 'infinite_chance_base', 'stock')),
        infinite_decay_scale=float(_require_value(_stock_cfg, 'infinite_decay_scale', 'stock')),
        infinite_decay_size_multiplier=float(_require_value(_stock_cfg, 'infinite_decay_size_multiplier', 'stock')),
        price_scale=float(_require_value(_stock_cfg, 'price_scale', 'stock')),
        size_scale=float(_require_value(_stock_cfg, 'size_scale', 'stock')),
        price_sensitivity=float(_require_value(_stock_cfg, 'price_sensitivity', 'stock')),
        size_sensitivity=float(_require_value(_stock_cfg, 'size_sensitivity', 'stock')),
        min_price_norm=float(_require_value(_stock_cfg, 'min_price_norm', 'stock')),
        min_size_norm=float(_require_value(_stock_cfg, 'min_size_norm', 'stock')),
        min_scale=float(_require_value(_stock_cfg, 'min_scale', 'stock'))
    )

generation = _load_generation_config()
demand = _load_demand_config()
markup = _load_markup_config()
transit = _load_transit_config()
logistics = _load_logistics_config()
stock = _load_stock_config()
guardrails = _load_guardrails_config()