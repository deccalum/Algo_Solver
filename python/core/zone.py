from typing import Protocol
from dataclasses import dataclass
import numpy as np

class ZoneMode(Protocol):
    """Protocol for zone value generation strategies."""
    
    def generate(
        self, start: float, end: float, zone: "Zones", guardrails
    ) -> list[float]: ...

@dataclass
class Exact:
    """Generate values at exact step intervals."""

    def generate(
        self, start: float, end: float, zone: "Zones", guardrails
    ) -> list[float]:
        span = max(guardrails.min_span, end - start)
        step = max(guardrails.min_step, zone.step)
        count = max(int(span / step) + 1, guardrails.min_count)
        values = np.linspace(start, end, count)
        return [float(v) for v in values]

@dataclass
class Power:
    """Generate values along a power curve (bias controls concentration)."""

    def generate(
        self, start: float, end: float, zone: "Zones", guardrails
    ) -> list[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        shaped = t ** max(guardrails.min_bias, zone.bias)
        values = start + (end - start) * shaped
        return [float(v) for v in values]

@dataclass
class Geometric:
    """Generate values in geometric progression."""

    def generate(
        self, start: float, end: float, zone: "Zones", guardrails
    ) -> list[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        if resolution <= 1:
            return [float(start)]

        safe_start = max(guardrails.min_safe_start, start)
        safe_end = max(safe_start, end)
        ratio = (safe_end / safe_start) ** (1.0 / (resolution - 1))
        return [safe_start * (ratio**i) for i in range(resolution)]

@dataclass
class Gaussian:
    """Gaussian-like distribution."""

    def generate(
        self, start: float, end: float, zone: "Zones", guardrails
    ) -> list[float]:
        resolution = max(guardrails.min_resolution, zone.resolution)
        t = np.linspace(0.0, 1.0, resolution)
        edge_dense = 0.5 - 0.5 * np.cos(np.pi * t)
        values = start + (end - start) * edge_dense
        return [float(v) for v in values]

MODE_REGISTRY: dict[str, ZoneMode] = {
    "exact": Exact(),
    "power": Power(),
    "geometric": Geometric(),
    "gaussian": Gaussian(),
}

@dataclass
class Zones:
    """Zone configuration used for value generation."""

    mode: ZoneMode
    span_share: float
    resolution: int
    bias: float
    step: float
