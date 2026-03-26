// TypeScript types generated from algsolver.proto
// These match the protobuf message structures

export interface Zone {
    mode: string;
    span_share: number;
    resolution: number;
    bias: number;
    step: number;
}

export interface ZoneDefaults {
    mode: string;
    span_share: number;
    resolution: number;
    bias: number;
    step: number;
}

export interface Generation {
    budget: number;
    space: number;
    min_price: number;
    max_price: number;
    min_size: number;
    max_size: number;
    price_zones: Zone[];
    size_zones: Zone[];
    zone_defaults: ZoneDefaults;
}

export interface Demand {
    base_demand: number;
    price_scale: number;
    size_scale: number;
    price_sensitivity: number;
    size_sensitivity: number;
    noise: number;
    min_demand: number;
    max_demand: number;
}

export interface Markup {
    base_rate: number;
    price_scale: number;
    max_rate: number;
    noise: number;
    price_divisor: number;
    min_rate: number;
    max_rate_clamp: number;
}

export interface TransitMode {
    name: string;
    capacity: number;
    base_cost: number;
    max_value_density: number;
    min_weight_class: number;
}

export interface Transit {
    courier: TransitMode;
    pallet: TransitMode;
    container: TransitMode;
    min_capacity_epsilon: number;
    weight_volume_ratio: number;
    origin: number;
    origin_zone: ZoneSpec;
}

export interface TransitResult {
    mode: string;
    capacity: number;
    cost: number;
}

export interface Logistics {
    min_size_log: number;
    penalty_factor: number;
    max_difficulty: number;
    optimal: number;
    base_cost: number;
}

export interface Stock {
    base_stock: number;
    min_stock: number;
    noise: number;
    infinite_stock_value: number;
    infinite_chance_base: number;
    infinite_decay_scale: number;
    infinite_decay_size: number;
    price_scale: number;
    size_scale: number;
    price_sensitivity: number;
    size_sensitivity: number;
    min_price_norm: number;
    min_size_norm: number;
    min_scale: number;
}

export interface Guardrails {
    min_span: number;
    min_step: number;
    min_resolution: number;
    min_bias: number;
    min_safe_start: number;
    min_count: number;
    round_min: number;
}

export interface AppConfig {
    generation: Generation;
    demand: Demand;
    markup: Markup;
    transit: Transit;
    logistics: Logistics;
    stock: Stock;
    guardrails: Guardrails;
}

export interface Product {
    id: string;
    price: number;
    size: number;
    logistics: number;
    transit: string;
    transit_size: number;
    transit_cost: number;
    demand: number;
    markup: number;
    stock: number;
}

export interface ZoneSpec {
    mode: string;
    span_share: number;
    resolution: number;
    step: number;
    bias: number;
}

export interface GenerateCatalogRequest {
    config: AppConfig;
}

export interface GenerateCatalogResponse {
    products: Product[];
    generated_count: number;
}

export interface OptimizeCatalogRequest {
    config: AppConfig;
    products: Product[];
}

export interface OptimizeCatalogResponse {
    status: string;
    objective_value: number;
    selected_count: number;
}

export interface RunPipelineRequest { }

export interface RunPipelineResponse {
    status: string;
    objective_value: number;
    generated_count: number;
    selected_count: number;
}

export interface EstimateRequest {
    price_min: number;
    price_max: number;
    size_min: number;
    size_max: number;
    price_zones: ZoneSpec[];
    size_zones: ZoneSpec[];
}

export interface EstimateResponse {
    estimated_products: number;
    strategy: string;
}