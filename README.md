# Algo Solver

## Architecture Overview

The system uses a **Generator-Manager-Engine** architecture to decouple data generation from mathematical optimization.


### 1. The Generator ([``candidate_generator.py``](python/candidate_generator.py))

- **Purpose**: Explores the entire theoretical parameter space defined in ([``parameter_core.json``](config/parameter_core.json)).
- **Function**: Combinatorially generates hundreds of thousands of potential product configurations (Price × Weight × Size).
- **Logic**: Applies heuristic "Reality Checks" to discard physically impossible items (e.g., a 20kg item costing $1).
- **Output**: Produces the raw pool of candidates (`product_candidates.csv`).

### 2. The Manager ([``optimization_manager.py``](python/optimization_manager.py))

- **Purpose**: Orchestrates the workflow and manages resources.
- **Function**:
  1. Reads the parameter core for settings.
  2. Loads candidates and applies a "Smart Filter" to select the top candidates (Top-N) to ensure the solver completes in reasonable time.
  3. Hires the **Engine** to perform the complex math.
- **Result**: Exports the final optimized catalog and purchase orders.

### 3. The Engine ([``optimization_engine.py``](python/optimization_engine.py))

- **Purpose**: Pure mathematical optimization using **Google OR-Tools** (SCIP Solver).
- **Logic**:
  - **Objective**: "Maximize Profit".
    ```math
    \text{Maximize: } \sum ((\text{Retail} - \text{Wholesale}) \times \text{Qty}) - \text{Shipping} - \text{Duties}
    ```
  - **Constraints**: Translates physical limits into strict math.
    ```math
    \sum (\text{Size} \times \text{Qty}) \le \text{Warehouse Capacity}
    ```
  - **Time Awareness**: Creates variables for every month (e.g., `q_P001_Month1`, `q_P001_Month2`), enabling seasonal planning (e.g. stocking up in October for December sales).
