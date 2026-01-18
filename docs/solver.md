# Inventory Optimizer - Solver Documentation

## Problem Formulation

**Decision Variables:**
- q[p,t] = quantity to order for product p in month t (Integer ≥ 0)

**Objective Function (Maximize):**

Profit = Σ_t Σ_p [(retail_p - wholesale_p) × q[p,t]]
- Σ_t [weight_shipping_t + volume_shipping_t + customs_t]


**Constraints:**
1. **Budget (per month t):** Σ_p (wholesale_p × q[p,t]) ≤ budget_t
2. **Warehouse capacity:** Σ_t Σ_p (size_p × q[p,t]) ≤ warehouse_m³
3. **Shipping weight (per month t):** Σ_p (weight_p × q[p,t]) ≤ max_weight_kg
4. **Shipping volume (per month t):** Σ_p (volume_p × q[p,t]) ≤ max_volume_m³
5. **Demand (per product p, month t):** q[p,t] ≤ forecast[p,t] × buffer

## Solver: SCIP

- **Type:** Branch-and-cut integer programming solver
- **Optimization:** COIN-OR SCIP (written in C)
- **Speed:** 100-1000 variables: <5 seconds; 10,000 variables: <60 seconds
- **License:** ZIB Academic License (free for non-commercial)
