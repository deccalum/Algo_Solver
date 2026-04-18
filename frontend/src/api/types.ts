// ── Request types ──

export interface ParamSpec {
  name: string;
  dist: string;
  min: number | null;
  max: number | null;
  values?: any[] | null;
  dist_kwargs: Record<string, number>;
}

export interface InfluenceSpec {
  source: string;
  target: string;
  fn: string;
  kwargs?: Record<string, number>;
}

export interface ConstraintSpec {
  name: string;
  kind: 'sum_le' | 'sum_ge' | 'sum_eq';
  param_name: string;
  bound: number;
}

export interface LogifierConfig {
  enabled: boolean;
  density_floor: number;
  density_ceiling: number;
  price_per_litre_ceiling: number;
  price_size_threshold: number;
}

export interface GenerateRequest {
  template?: string;
  params?: ParamSpec[];
  influences?: InfluenceSpec[];
  overrides?: Record<string, any>;
  limit?: number;
  logifier?: LogifierConfig;
}

export interface SpecifiedProduct {
  name: string;
  price: number;
  amount: number;
  volume: number;
  weight?: number | null;
}

export interface SolveRequest {
  generation_run_id?: string;
  template?: string;
  params?: ParamSpec[];
  influences?: InfluenceSpec[];
  overrides?: Record<string, any>;
  constraints?: ConstraintSpec[];
  objective_param?: string;
  objective_sense?: 'maximize' | 'minimize';
  limit?: number;
  specified_products?: SpecifiedProduct[];
}

// ── Response types ──

export interface TemplateInfo {
  name: string;
  combination_count: number;
  params: ParamSpec[];
  influences: InfluenceSpec[];
  constraints: ConstraintSpec[];
  objective_param: string;
  objective_sense: 'maximize' | 'minimize';
}

export interface CountResponse {
  count: number;
  limit: number;
  ok: boolean;
}

export interface GenerateResponse {
  run_id: string;
  template_name: string;
  item_count: number;
}

export interface SolveResponse {
  solve_id: string;
  generation_run_id: string;
  objective_value: number;
  selected_count: number;
  total_generated: number;
}

export interface RunSummary {
  id: string;
  template_name: string | null;
  item_count: number;
  created_at: string;
  params: ParamSpec[];
}

export interface RunDetail extends RunSummary {
  influences: InfluenceSpec[];
  solve_runs: { id: string; objective_value: number; selected_count: number; created_at: string }[];
}

export interface RunItems {
  run_id: string;
  total: number;
  offset: number;
  limit: number;
  items: { id: number; item_id: string; data: Record<string, any> }[];
}

export interface SolveSummary {
  id: string;
  generation_run_id: string;
  objective_param: string;
  objective_sense: string;
  objective_value: number;
  selected_count: number;
  created_at: string;
}

export interface SolveDetail extends SolveSummary {
  constraints: ConstraintSpec[];
  selections: { item_id: number; data: Record<string, any> }[];
}

export interface TableInfo {
  name: string;
  row_count: number;
}

export interface ColumnInfo {
  column: string;
  type: string;
}

export interface TableData {
  total: number;
  offset: number;
  limit: number;
  data: Record<string, any>[];
}

// ── Simulation ──

export interface SimConfig {
  time_horizon?:      number;
  space_capacity?:    number;
  space_buffer?:      number;
  lead_time?:         number;
  budget?:            number;
  reorder_threshold?: number;
}

export interface SimulateRequest {
  solve_id: string;
  config?:  SimConfig;
}

export interface DaySnapshot {
  day:             number;
  stock:           Record<string, number>;
  units_sold:      Record<string, number>;
  units_received:  Record<string, number>;
  units_ordered:   Record<string, number>;
  space_used:      number;
  space_available: number;
  action:          string;
  log_level:       'ok' | 'info' | 'warn';
  log_text:        string;
}

export interface SimulateResponse {
  solve_id:     string;
  time_horizon: number;
  days:         DaySnapshot[];
}

// ── Solar ──
export interface SolarPshResponse {
  lat:               number;
  tilt_used:         number;
  azimuth_used:      number;
  optimal_azimuth:   string;
  date:              string;
  psh:               number;
  annual_avg_psh:    number;
  seasonal_min_psh:  number;
  seasonal_max_psh:  number;
  azimuth_gain_pct?: number;
}

export interface SolarSolveRequest {
  lat:                  number;
  tilt?:                number | null;
  azimuth?:             number | null;
  electricity_rate:     number;
  feed_in_rate:         number;
  upfront_budget:       number;
  max_monthly?:         number | null;
  battery_cost_per_kwh: number;
  roof_area_m2:         number;
  panel_area_m2:        number;
  system_lifetime:      number;
  daily_kwh:            number;
}

export interface SolarSolveResponse {
  solve_id:          string;
  generation_run_id: string;
  objective_value:   number;
  selected_count:    number;
  total_generated:   number;
  sunlight_hours_used: number;
  n_panels:          number;
  azimuth_used:      number;
  optimal_azimuth:   string;
  upfront_budget:    number;
  system_cost:       number;
  annual_savings:    number;
  payback_years:     number | null;
  system_lifetime:   number;
  selections:        Record<string, any>[];
  alternatives:      Record<string, any>[];
  azimuth_gain_pct?: number;
}

export type SimStreamMessage =
  | { type: 'meta'; solve_id: string; time_horizon: number; item_count: number }
  | ({ type: 'day' } & DaySnapshot)
  | { type: 'done' };
