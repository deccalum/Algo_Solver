// fieldInfo.js — real-world context for generation parameter tooltips.

export const FIELD_INFO = {
  // ── generic_product params ────────────────────────────────────────────────
  price: {
    range: "Typical retail products: $1 (commodity staple) → $500 (mid-range electronics) → $10,000 (premium/specialist equipment). Most SKUs cluster under $200.",
    distribution: "Power distribution (bias toward min) reflects real markets: many cheap items, few expensive ones.",
  },
  weight: {
    range: "Consumer goods: 10 g (pen) → 500 g (tablet) → 5 kg (small appliance) → 50 kg (heavy equipment). Average parcel weight ≈ 2 kg.",
    distribution: "Gaussian centred around typical product weight for the category.",
    bound: "Weight limits: standard truck ≈ 24,000 kg total · air freight pallet ≈ 1,000 kg · typical shelf bay 50–200 kg · retail unit load ≈ 500 kg.",
  },
  volume: {
    range: "0.001 m³ (1 L bottle or small box) → 0.01 m³ (laptop bag) → 0.1 m³ (mini-fridge) → 1 m³ (large wardrobe). Pallet positions are ≈ 1.2 m³.",
    distribution: "Uniform spread captures variety across a product range.",
    bound: "Storage sizes: back office 10–50 m³ · SME warehouse 100–500 m³ · medium warehouse 500–2,000 m³ · regional DC 5,000–15,000 m³ · large FC (Amazon-scale) 50,000+ m³. One pallet bay ≈ 1.5 m³ → 50 m³ ≈ 33 bays.",
  },
  demand: {
    range: "Weekly unit demand: 1 (niche/luxury) → 50 (mid-volume) → 500 (fast-moving consumer good, FMCG). High-volume staples exceed 1,000/week.",
    distribution: "Power distribution: few high-demand items, many low-demand items.",
  },

  // ── solar_panel params ────────────────────────────────────────────────────
  efficiency: {
    range: "Commercial silicon panels: 15% (budget mono-Si) → 19% (mainstream) → 23% (premium HJT/IBC). Lab records exceed 26%. Most off-the-shelf panels are 17–21%.",
    distribution: "Uniform spread covers the realistic commercial band.",
    bound: "Minimum viable efficiency for a rooftop install is typically ≥ 17%. Below that the area required becomes impractical for most sites.",
  },
  cost_per_watt: {
    range: "Installed $/W: $0.20 (utility-scale wholesale panels) → $0.40 (commercial) → $0.80 (residential retail including installation). Premium panels with higher efficiency push toward $1.00/W.",
    distribution: "Power distribution: many cheaper commodity options, few premium.",
    bound: "Budget constraint as total $/W across selected configurations. A typical residential system at $0.40/W × 10 kW = $4,000.",
  },
  sunlight_hours: {
    range: "Peak sun hours per day: 3 h (northern Europe, winter) → 5 h (mid-latitude average) → 8 h (equatorial / desert regions). Drives energy yield calculations. Use the location tool to compute site-specific values from coordinates.",
    distribution: "Uniform spread across geographic/seasonal scenarios.",
    bound: "Minimum total peak sun hours required across all selected panel configurations. Ensures the overall mix has adequate solar resource.",
  },
  degradation_rate: {
    range: "Annual efficiency loss (%/yr): 0.3% (premium HJT/IBC panels, 25-yr warranty) → 0.5% (mainstream mono-Si) → 0.8% (budget or older technology). Industry median is ~0.5%/yr. Over 25 years at 0.5%/yr, a panel retains ~88% of its original yield on average.",
    distribution: "Uniform spread across the commercial quality band.",
  },

  // ── production_line params ────────────────────────────────────────────────
  labour_hours: {
    range: "Hours per shift or per batch: 1 h (automated micro-task) → 8 h (standard shift) → 24 h (continuous operations). Most production tasks fall in the 2–12 h range.",
    distribution: "Uniform spread covers the practical scheduling range.",
    bound: "Total available labour hours per week. Standard: 40 h (one FTE) · 80 h (two shifts) · 168 h (fully continuous). Overtime kicks in above 40 h.",
  },
  machine_capacity: {
    range: "Units per hour or batch capacity: 100 (small benchtop machine) → 1,000 (mid-scale line) → 10,000 (high-throughput automated line). CNC machines ≈ 200–2,000 u/h.",
    distribution: "Step distribution with 100-unit increments reflects discrete machine specifications.",
    bound: "Maximum available machine-hours or capacity units per cycle.",
  },
  material_cost: {
    range: "Cost per unit of material input: $0.50 (bulk commodity) → $5 (engineered component) → $50 (precision part or specialty chemical). Most manufacturing materials are $1–$20/unit.",
    distribution: "Power distribution: many cheap materials, few expensive specialty inputs.",
    bound: "Total material budget per production run ($). Typical batch: $50–$500 for small-scale · $1,000–$10,000 for mid-scale.",
  },
  throughput: {
    range: "Units produced per hour: 10 (artisan / manual) → 100 (semi-automated) → 1,000 (fully automated line). Influenced by both labour and machine capacity.",
    distribution: "Uniform baseline; actual values are shifted by labour and machine influence rules.",
  },

  // ── Constraints ───────────────────────────────────────────────────────────
  budget: {
    bound: "Typical procurement budgets: $5,000 (small team) · $25,000 (medium run) · $250,000 (quarterly category spend) · $1M+ (enterprise). A $25k budget covers ≈ 50 mid-range items.",
  },
  space: {
    bound: "Warehouse sizes: small storage unit 10–50 m³ · SME warehouse 500–2,000 m³ · medium DC 5,000–15,000 m³ · large DC 50,000+ m³. A standard pallet bay ≈ 1.5 m³.",
  },
  labour: {
    bound: "Total available labour hours per scheduling period. Standard: 40 h/week per FTE · 80 h (two-shift) · 120 h (three-shift). Overtime is typically capped at 20% above the standard.",
  },
  materials: {
    bound: "Total material spend per production cycle ($). Scales with batch size and material unit costs. Typical SME run: $100–$1,000.",
  },
  sunlight: {
    bound: "Minimum total peak sun hours required across all selected panel configurations. Ensures the overall mix has adequate solar resource. Use the location calculator to derive a realistic value for your site.",
  },
  roof_area: {
    bound: "Proxy for total installation area: limits the sum of efficiency values across selected configurations, indirectly bounding how many high-efficiency (physically larger) panels are chosen. Typical residential roof: 20–40 m² usable area.",
  },
  energy_value: {
    hint: "Computed objective: (efficiency/100 × sunlight_hours × lifetime_yield_factor) / cost_per_watt. Represents lifetime energy output per dollar invested. Higher = better return. The solver maximises this across all viable configurations.",
  },

  // ── Realism filter ────────────────────────────────────────────────────────
  density_floor: {
    hint: "Very low densities are physically unusual for retail goods. Reference: aerogel ≈ 2 kg/m³, foam packing ≈ 30–80 kg/m³, cork ≈ 120 kg/m³. Below 50 kg/m³ is rare outside specialty materials.",
  },
  density_ceiling: {
    hint: "Very high densities exclude implausible combinations. Reference: water = 1,000 kg/m³ · aluminium = 2,700 · steel = 7,850 · lead = 11,340 · osmium = 22,590. Most consumer goods are 100–3,000 kg/m³.",
  },
  price_per_m3: {
    hint: "Tiny, expensive items stretch plausibility. A 0.001 m³ (1L) item at $5,000 = $5M/m³ — plausible for perfume or electronics. At $50,000 = $50M/m³ — jewellery territory. Use this to filter unrealistic combinations.",
  },
  size_threshold: {
    hint: "The $/m³ rule only fires for items below this volume. 0.001 m³ = 1 L (wine bottle) · 0.01 m³ = 10 L (bucket) · 0.1 m³ = 100 L (large bag). Large items naturally have higher absolute prices, so the rule is not applied.",
  },
};
