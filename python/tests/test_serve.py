"""
test_serve.py — pipe test commands to `python main.py serve`

Usage:
    python test_serve.py | python main.py serve
"""
import json
import sys

def send(obj):
    print(json.dumps(obj), flush=True)

# ── Test 1: count well within limit ───────────────────────────────────────────
send({"command": "count", "params": [
    {"name": "price", "dist": "power",   "min": 10,  "max": 1000, "dist_kwargs": {"resolution": 20}},
    {"name": "size",  "dist": "uniform", "min": 1,   "max": 500,  "dist_kwargs": {"resolution": 15}},
]})

# ── Test 2: count that exceeds the limit ───────────────────────────────────────
send({"command": "count", "params": [
    {"name": "price",     "dist": "power",    "min": 10,  "max": 1000, "dist_kwargs": {"resolution": 200}},
    {"name": "size",      "dist": "gaussian", "min": 1,   "max": 500,  "dist_kwargs": {"resolution": 150}},
    {"name": "demand",    "dist": "uniform",  "min": 0.1, "max": 10,   "dist_kwargs": {"resolution": 100}},
    {"name": "logistics", "dist": "step",     "min": 1,   "max": 100,  "dist_kwargs": {"step": 0.5}},
]})

# ── Test 3: generate refused because limit exceeded ────────────────────────────
send({"command": "generate", "params": [
    {"name": "price", "dist": "power",   "min": 10, "max": 1000, "dist_kwargs": {"resolution": 1500}},
    {"name": "size",  "dist": "uniform", "min": 1,  "max": 500,  "dist_kwargs": {"resolution": 1500}},
]})

# ── Test 4: small generate — streams products ──────────────────────────────────
send({"command": "generate", "params": [
    {"name": "price", "dist": "step",    "min": 10, "max": 50,  "dist_kwargs": {"step": 10}},
    {"name": "size",  "dist": "uniform", "min": 1,  "max": 10,  "dist_kwargs": {"resolution": 3}},
]})

# ── Test 5: generate with influence ───────────────────────────────────────────
send({"command": "generate", "params": [
    {"name": "price",  "dist": "step",    "min": 10, "max": 50, "dist_kwargs": {"step": 10}},
    {"name": "demand", "dist": "uniform", "min": 1,  "max": 5,  "dist_kwargs": {"resolution": 3}},
], "influences": [
    {"source": "price", "target": "demand", "fn": "scale", "kwargs": {"factor": -0.01}},
]})

# ── Test 6: bad JSON — should get error response ───────────────────────────────
print("not valid json {{{", flush=True)

# ── Test 7: unknown command ────────────────────────────────────────────────────
send({"command": "explode", "params": []})
