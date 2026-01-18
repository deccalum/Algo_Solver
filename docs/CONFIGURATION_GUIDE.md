# Configuration Guide

## Quick Reference

Plan to adhere all values to `config/config.cfg`.

---

## Demand Model Tiers

Each price tier has independent demand characteristics:

```json
"demand_model": {
  "tiers": [
    {
      "tier_name": "ultra_cheap",
      "min_price": 0.0,
      "max_price": 5.0,
      "base_demand_monthly": 300,      // Starting demand before adjustments
      "max_demand_monthly": 1000,      // Hard cap - optimizer won't order more
      "demand_multiplier": 1.3         // Tier-specific elasticity (1.0 = neutral)
    },
    ...
  ]
}
```

**Tuning Demand**:
- Lower `base_demand_monthly`: Less interest in this price tier
- Lower `max_demand_monthly`: Capacity constraints (storage, supply)
- Lower `demand_multiplier`: Market saturation (0.6 = pessimistic, 1.3 = optimistic)

---

## Markup Tiers

Markup multipliers applied based on wholesale cost:

```json
"markup_tiers": [
  {
    "min_cost": 0.0,
    "max_cost": 5.0,
    "markup_multiplier": 3.5  // 250% markup for cheap items
  },
  {
    "min_cost": 500.0,
    "max_cost": 999999.0,
    "markup_multiplier": 1.3  // 30% markup for luxury items
  }
]
```

Higher markups on cheaper items (standard retail practice).

---

## Seasonal Factors

Demand multipliers by month (1.0 = baseline):

```json
"seasonal_factors": {
  "1": 0.8,    // January: 20% lower demand
  "6": 1.0,    // June: Normal demand
  "12": 1.6    // December: 60% higher demand
}
```

---

## Shipping Configuration

```json
"shipping": {
  "name": "Express International",
  "cost_per_kg": 3.5,           // $/kg surcharge
  "cost_per_m3": 80.0,          // $/m³ surcharge
  "max_weight_kg": 800.0,       // Weight limit per shipment
  "max_volume_m3": 15.0,        // Volume limit per shipment
  "crosses_border": true,        // Customs duty applies
  "customs_duty_rate": 0.12,    // 12% tax on import
  "days_transit": 3             // Delivery time
}
```

---

## Optimization Parameters

```json
"planning_months": 3,            // Planning horizon (months)
"budget_per_month": 12000.0,    // Monthly purchasing budget ($)
"warehouse_capacity_m3": 40.0,  // Storage limit (m³)
"solver_type": "SCIP",          // Optimizer engine
"solver_time_limit_seconds": 300 // Max optimization time
```

---