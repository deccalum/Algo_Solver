# Product Parameter Optimization - Usage Guide

## Overview

This system generates and optimizes product parameters using integer programming. Two approaches are available depending on your hardware capabilities.

---

## Quick Start

### Option 1: Batch Optimization (Fast, High-Memory)
**Best for:** Systems with 8GB+ RAM, need fastest results  
**Time:** ~5-30 minutes for 1.5M candidates  
**Memory:** ~2-10GB RAM

```bash
# Generate full candidate set (1.5M products)
python productcreator.py --filter-mode full

# Run batch optimization
python batch_optimizer.py product_candidates --top-n 100
```

### Option 2: Filtered Optimization (Safe, Low-Memory)
**Best for:** Any machine, guaranteed to work  
**Time:** ~2-5 minutes for 10k candidates  
**Memory:** <1GB RAM

```bash
# All-in-one: generate filtered candidates + optimize
python filtered_optimizer.py --filter-mode aggressive --top-n 50
```

---

## Detailed Usage

### 1. Product Candidate Generation (`productcreator.py`)

Generate all feasible product parameter combinations with configurable filtering.

**Command:**
```bash
python productcreator.py [options]
```

**Options:**
- `--filter-mode {full|medium|aggressive}` - Filtering preset (default: full)
  - `full`: ~1.5M candidates (price: $1-$10k, weight: 0.1-100kg, size: 100-50k cm³)
  - `medium`: ~100k candidates (price: $5-$5k, coarser steps)
  - `aggressive`: ~10k candidates (price: $10-$1k, coarsest steps)
- `--output FILENAME` 

---

### 2a. Batch Optimizer (`batch_optimizer.py`) - Option 1

Runs optimizer ONCE with all candidates. The solver selects the optimal subset.

**Command:**
```bash
python batch_optimizer.py CANDIDATES_FILE [options]
```

**Arguments:**
- `CANDIDATES_FILE`

**Options:**
- `--output FILENAME`
- `--results-output FILENAME`
- `--top-n N` - Limit to top N products (default: all selected)
- `--budget AMOUNT` - Monthly budget (default: 12000)
- `--warehouse-capacity M3` - Warehouse capacity in m³ (default: 40)
- `--planning-months N` - Planning horizon (default: 3)

---

### 2b. Filtered Optimizer (`filtered_optimizer.py`) - Option 2

All-in-one script: generates filtered candidates + optimizes. Safe for any machine.

**Command:**
```bash
python filtered_optimizer.py [options]
```

**Options:**
- `--filter-mode {medium|aggressive}` - Filter preset (default: aggressive)
- `--top-n N` - Top N products to export (default: 50)
- `--output FILENAME` - Catalog file (default: filtered_catalog.json)
- `--results-output FILENAME` - Full results (default: filtered_optimization_results)
- `--budget AMOUNT` - Monthly budget (default: 12000)
- `--warehouse-capacity M3` - Warehouse capacity (default: 40)
- `--planning-months N` - Planning horizon (default: 3)
- `--skip-generation` - Use existing filtered_candidates

---