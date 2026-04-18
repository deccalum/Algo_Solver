# simulation.py — procurement simulation engine
from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass, field

from python.solver import optimize, SolveRequest, ConstraintSpec, ConstraintKind, Sense


# ── Config ────────────────────────────────────────────────────────────────────
@dataclass
class SimConfig:
    time_horizon:      int   = 30       # days to simulate
    space_capacity:    float = 500.0    # m³ total warehouse capacity
    space_buffer:      float = 0.15     # fraction reserved as safety headroom
    lead_time:         int   = 3        # supplier lead time in days
    budget:            float = 50_000.0 # per-reorder budget ceiling ($)
    reorder_threshold: float = 0.25     # reorder when free space > this fraction


# ── Per-product state ─────────────────────────────────────────────────────────
@dataclass
class InventoryState:
    product_id:  str
    on_hand:     int
    daily_rate:  float                            # expected daily demand (units/day)
    volume_each: float                            # m³ per unit
    price_each:  float                            # $ per unit
    inbound:     list[tuple[int, int]] = field(default_factory=list)  # (arrival_day, qty)


# ── Day output ────────────────────────────────────────────────────────────────
@dataclass
class DaySnapshot:
    day:             int
    stock:           dict[str, int]     # product_id → units on hand
    units_sold:      dict[str, int]
    units_received:  dict[str, int]
    units_ordered:   dict[str, int]
    space_used:      float              # m³ currently on hand
    space_available: float              # m³ available for new orders
    action:          str                # "HOLD" | "BUY (N units)" | …
    log_level:       str                # "ok" | "info" | "warn"
    log_text:        str


# ── Low-level helpers ─────────────────────────────────────────────────────────
def _receive_inbound(s: InventoryState, day: int) -> tuple[InventoryState, int]:
    """Move orders arriving today into on-hand stock."""
    arriving  = sum(qty for d, qty in s.inbound if d == day)
    remaining = [(d, qty) for d, qty in s.inbound if d != day]
    return dataclasses.replace(s, on_hand=s.on_hand + arriving, inbound=remaining), arriving


def _project_demand(s: InventoryState) -> int:
    """Sample actual sales from daily_rate with 15 % Gaussian noise."""
    if s.on_hand <= 0 or s.daily_rate <= 0:
        return 0
    expected = min(s.daily_rate, float(s.on_hand))
    sigma    = max(0.5, expected * 0.15)
    return min(s.on_hand, max(0, round(random.gauss(expected, sigma))))


def _space_on_hand(stock: dict[str, InventoryState]) -> float:
    return sum(s.on_hand * s.volume_each for s in stock.values())


def _available_space(stock: dict[str, InventoryState], config: SimConfig) -> float:
    """Warehouse capacity minus on-hand stock minus safety buffer."""
    used   = _space_on_hand(stock)
    buffer = config.space_capacity * config.space_buffer
    return max(0.0, config.space_capacity - used - buffer)


def _make_reorder_items(items: list[dict], lead_time: int) -> list[dict]:
    """
    Scale each item's price and volume by its planned reorder quantity
    (demand * lead_time) so the solver's budget/space constraints reflect the
    cost and footprint of a full replenishment batch.
    """
    result = []
    for item in items:
        qty = max(1, round(item.get("demand", 1.0) * lead_time))
        result.append({
            **item,
            "price":        item.get("price",  0.0) * qty,
            "volume":       item.get("volume", 0.0) * qty,
            "_reorder_qty": qty,
        })
    return result


def _init_stock(items: list[dict], config: SimConfig) -> dict[str, InventoryState]:
    """Seed initial inventory at demand × lead_time × 2 units per product."""
    return {
        item["id"]: InventoryState(
            product_id  = item["id"],
            on_hand     = max(1, round(item.get("demand", 1.0) * config.lead_time * 2)),
            daily_rate  = item.get("demand",  1.0),
            volume_each = item.get("volume",  0.1),
            price_each  = item.get("price",   0.0),
        )
        for item in items
    }


# ── Engine ────────────────────────────────────────────────────────────────────
def run_simulation_iter(items: list[dict], config: SimConfig):
    """
    Generator: yield one DaySnapshot per simulated day.

    items: product dicts from a solve result's selections.
           Required keys: id, price, volume, demand (daily units).

    Used by the streaming API endpoint; collect with list() for batch use.
    """
    if not items:
        return

    stock         = _init_stock(items, config)
    reorder_items = _make_reorder_items(items, config.lead_time)

    for day in range(1, config.time_horizon + 1):
        # 1. Receive inbound orders
        units_received: dict[str, int] = {}
        for pid in list(stock):
            stock[pid], received = _receive_inbound(stock[pid], day)
            units_received[pid] = received

        # 2. Realise demand (Gaussian noise)
        units_sold: dict[str, int] = {}
        for pid in list(stock):
            sold = _project_demand(stock[pid])
            units_sold[pid] = sold
            stock[pid] = dataclasses.replace(stock[pid], on_hand=max(0, stock[pid].on_hand - sold))

        # 3. Decide reorder
        space_used = _space_on_hand(stock)
        avail      = _available_space(stock, config)
        fill_ratio = space_used / config.space_capacity if config.space_capacity > 0 else 1.0
        free_ratio = 1.0 - fill_ratio

        units_ordered: dict[str, int] = {}
        action    = "HOLD"
        log_level = "ok"
        log_text  = f"SOLVING... space at {fill_ratio:.0%} — holding"

        if free_ratio > config.reorder_threshold:
            result = optimize(SolveRequest(
                items           = reorder_items,
                constraints     = [
                    ConstraintSpec("budget", ConstraintKind.SUM_LE, "price",  config.budget),
                    ConstraintSpec("space",  ConstraintKind.SUM_LE, "volume", avail),
                ],
                objective_param = "demand",
                objective_sense = Sense.MAXIMIZE,
            ))
            if result.selections:
                for sel in result.selections:
                    pid = sel["id"]
                    qty = sel.get("_reorder_qty", max(1, round(sel.get("demand", 1) * config.lead_time)))
                    units_ordered[pid] = qty
                    if pid in stock:
                        s = stock[pid]
                        stock[pid] = dataclasses.replace(s, inbound=s.inbound + [(day + config.lead_time, qty)])
                total_qty = sum(units_ordered.values())
                action    = f"BUY ({total_qty} units)"
                log_level = "info"
                log_text  = (
                    f"RE-ORDER: {total_qty} units across {len(units_ordered)} SKUs"
                    f" → arrives day {day + config.lead_time}"
                )
            else:
                log_text = f"SOLVING... no profitable reorder (avail={avail:.1f} m³)"

        # 4. Flag stockouts
        stockouts = [pid for pid, s in stock.items() if s.on_hand <= 0]
        if stockouts:
            log_level = "warn"
            log_text  = f"STOCKOUT: {len(stockouts)} SKU(s) depleted on day {day}"

        yield DaySnapshot(
            day             = day,
            stock           = {pid: s.on_hand for pid, s in stock.items()},
            units_sold      = units_sold,
            units_received  = units_received,
            units_ordered   = units_ordered,
            space_used      = space_used,
            space_available = avail,
            action          = action,
            log_level       = log_level,
            log_text        = log_text,
        )


def run_simulation(items: list[dict], config: SimConfig) -> list[DaySnapshot]:
    """Collect all DaySnapshots from run_simulation_iter into a list."""
    return list(run_simulation_iter(items, config))
