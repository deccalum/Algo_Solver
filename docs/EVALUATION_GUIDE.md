# Product Optimization Evaluation Guide

## Understanding the Optimization Results

The optimizer generates a product catalog with full parameters and profitability metrics. This guide explains how to interpret results and evaluate realism.

---

## Output Files

### CSV Catalog (`*_catalog.csv`)

| Column | Meaning | Why It Matters |
|--------|---------|----------------|
| `product_id` | Unique product identifier | Used to track products across runs |
| `name` | Generated product name | Reference (e.g., "Product_123") |
| `wholesale_price` | Cost to store | Higher margin = higher wholesale |
| `retail_price` | Price to customer | Derived from wholesale + markup tier |
| `weight_g` | Weight in grams | Affects shipping costs |
| `size_cm3` | Volume in cm³ | Affects warehouse utilization |
| `shipping_cost_multiplier` | Shipping cost factor | 1.0 (cheap), 2.5 (medium), 5.0 (heavy) |
| `base_demand` | Estimated monthly demand | Lower price = higher demand |
| `total_quantity_ordered` | Units ordered across all months | **Key profitability driver** |
| `total_cost` | Total wholesale cost across 3 months | Budget consumed |
| `total_revenue` | Total retail revenue across 3 months | Revenue generated |
| `total_margin` | Gross profit (revenue - cost) | **How profitable the product is** |

---

## Key Metrics to Evaluate

### 1. Margin per Product
```
Margin = Total Revenue - Total Cost
Example: $35,282 for P005113 across 3 months
```

**What it means:**
- High margin products are prioritized by optimizer
- Should be ranked by total_margin (descending) in results

**Red flags:**
- Extremely high margin (>200%) suggests unrealistic parameters
- Very low margin (<10%) suggests inefficient inventory use

### 2. Quantity Ordered
```
The more units ordered of a product, the higher the implied demand
Example: P005113 orders 767 units (seems high - verify)
```

**What it means:**
- Products with high base_demand get larger order quantities
- Directly influences total revenue and margin

**Reality check:**
- P000133 orders 1,267 units/year (105/month) - is demand realistic?
- Compare to wholesale_price: cheaper items should have higher quantities

### 3. Budget Utilization
```
Total Cost across all selected products ≤ Budget × Planning Months
Example: If budget=$12k/month × 3 months = $36k total, check sum of total_cost
```

**What it means:**
- Optimizer respects budget constraints
- Products are ranked by profitability within budget limits

### 4. Warehouse Utilization
```
Total Volume = Sum of (size_cm3 × quantity) across all products
Should be ≤ warehouse_capacity_m3 × 1,000,000
```

**Warehouse space example:**
- Capacity: 40 m³ = 40,000,000 cm³
- If selecting 12 products with diverse sizes, utilization should be reasonable

---

## Demand Realism: The Multiplier Problem

### Current Implementation (Demand Multiplier)
The optimizer uses `base_demand × demand_multiplier` to scale all products equally.

**Current behavior:**
- `base_demand` is estimated from product price/size/weight
- Multiplier of 1.0 = baseline forecast
- **Problem**: Applies uniformly; doesn't reflect real market dynamics

### Why Demand Matters
```
Total Units Ordered = base_demand × demand_multiplier × planning_months

Example (P005113 - Laptop Pro):
- base_demand = 30 units/month
- demand_multiplier = 1.0
- planning_months = 3
- Total ordered = 30 × 1.0 × 3 = 90 units (but result shows 767 - discrepancy!)
```

**The discrepancy suggests:**
- Optimizer is ordering aggressively due to high profitability ($35,282 margin!)
- Not limited by base_demand alone

### How to Test Demand Realism

**Option A: Conservative Scenario (0.5x multiplier)**
```bash
# Debug preset available in VS Code
python filtered_optimizer.py --demand-multiplier 0.5 --output conservative.json
```

**Interpret results:**
- If profit drops 30-50% → demand is moderately realistic
- If profit drops 80%+ → base model may be too optimistic

**Option B: Aggressive Scenario (1.5x-2.0x multiplier)**
```bash
python filtered_optimizer.py --demand-multiplier 1.5 --output aggressive.json
```

**Interpret results:**
- How much does margin increase?
- Does warehouse utilization exceed capacity?

**Option C: Compare Multiple Runs**
Create sensitivity analysis:
```bash
# Run 4 scenarios
python filtered_optimizer.py --demand-multiplier 0.5 --output scenarios/dem_0.5x.json
python filtered_optimizer.py --demand-multiplier 1.0 --output scenarios/dem_1.0x.json
python filtered_optimizer.py --demand-multiplier 1.5 --output scenarios/dem_1.5x.json
python filtered_optimizer.py --demand-multiplier 2.0 --output scenarios/dem_2.0x.json
```

Then compare:
- Total profit
- Number of products selected
- Average margin per product
- Warehouse space used

---

## Evaluating Your Current Results

### Results Summary
```
Status: OPTIMAL
Objective Value (Net Profit): $88,137.00
Products Selected: 12
```

**Analysis:**
- Status is OPTIMAL = best possible solution found
- $88k net profit seems reasonable for $36k budget (3 months × $12k)
- Only 12 products selected - is this enough variety?

### Top Product (P005113: $35,282 margin)
```
wholesale_price: $800
retail_price: $1,200
weight_g: 2,000
size_cm3: 30,000
base_demand: 30/month
total_quantity_ordered: 767 units
```

**Reality check:**
- 767 units of $800 laptops = $613k total cost
- At $1,200 retail = $920k revenue
- Margin = $307k (not $35k) - **CSV output may be aggregating differently**
- **Action**: Check if "total_margin" means per-month or cumulative

### Secondary Products (P000133-137: ~$11k margin each)
All have same parameters:
```
wholesale_price: ~$10-30 (estimated)
total_quantity_ordered: 1,267 units (very high!)
```

**Reality check:**
- 1,267 units/3 months = 422 units/month
- For a $20 product = $8,440/month revenue
- Margin of $11k/quarter seems reasonable
- **Pattern**: Optimizer heavily favors high-volume, lower-price items

---

## Improving Demand Estimates

### Current (Simplistic) Approach
```python
base_demand = {
    '$1-5': 200,
    '$5-20': 150,
    '$20-50': 100,
    # ... etc
}
```

**Issues:**
- Ignores market saturation
- Doesn't model price elasticity
- Same demand for expensive vs cheap items in same price tier
- No seasonal/category variation

### Recommended Improvements

**1. Price Elasticity (Inverse relationship)**
```python
# Cheaper items sell more
base_demand = 100 / (1 + 0.1 * log(wholesale_price))
```

**2. Category-Based Demand**
```python
category_demand = {
    'Electronics': 1.2,      # High demand
    'Clothing': 1.0,         # Baseline
    'Home': 0.8,             # Lower demand
    'Luxury': 0.5            # Very selective
}
```

**3. Seasonal Adjustment**
```python
seasonal_factors = {
    1: 0.7,   # January slow
    12: 1.8   # December peak
}
```

**4. Competitor Pricing (External data)**
```python
if wholesale_price < competitor_avg:
    demand_boost = 1.3  # Lower prices = higher demand
```

---

## Testing Workflow

### Step 1: Generate Scenarios
Run optimization with multiple demand multipliers:

```bash
cd /Users/gast/Programming/online_shop

# Conservative
python src/main/filtered_optimizer.py --filter-mode aggressive \
  --demand-multiplier 0.5 --output output/scenario_conservative.json

# Baseline
python src/main/filtered_optimizer.py --filter-mode aggressive \
  --demand-multiplier 1.0 --output output/scenario_baseline.json

# Optimistic
python src/main/filtered_optimizer.py --filter-mode aggressive \
  --demand-multiplier 1.5 --output output/scenario_optimistic.json
```

### Step 2: Compare Results

**Compare columns:**
- `total_quantity_ordered` - Should increase with demand_multiplier
- `total_margin` - Should increase proportionally
- Product selection - Do same products appear in all scenarios?

### Step 3: Validation Questions

1. **Do the top products make business sense?**
   - Why does P005113 (laptops) beat all others?
   - Is it really 8x more profitable than mid-tier products?

2. **Is quantity realistic?**
   - 767 laptops in 3 months = 256/month
   - Is this physically shippable? (2000g each = 512 tons/month)
   - **Reality check**: Most online shops move 10-100 units/month per SKU

3. **Warehouse utilization realistic?**
   - 767 × 30,000cm³ = 23M cm³ = 23 m³ for ONE product
   - Capacity is 40 m³ total
   - Other 11 products must fit in 17 m³ remaining

4. **Budget consumption reasonable?**
   - If P005113 uses $613k budget but limit is $36k/quarter...
   - **MAJOR RED FLAG** - Check if optimizer is respecting constraints

---

## Next Steps

### If Results Seem Unrealistic:

1. **Check constraint violations**

2. **Run with stricter parameters**

3. **Enable solver debugging**

---

## Key Takeaways

| Aspect | Current Status | Recommendation |
|--------|---|---|
| **Demand Model** | Simplistic (price-based only) | Add elasticity, category, seasonality |
| **Multiplier** | Hardcoded to 1.0 | Use CLI `--demand-multiplier` to test scenarios |
| **Evaluation** | Manual inspection only | Create sensitivity analysis with 3-5 scenarios |
| **Reality Check** | Spot-check top products | Compare to industry benchmarks |
| **Integration** | Not yet tested in Java | Merge CSV into simulator and validate profit predictions |

**Action**: Run scenario analysis (0.5x, 1.0x, 1.5x demand) and compare results. Document findings.
