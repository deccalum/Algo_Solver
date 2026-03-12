import math
import random

from dataclasses import dataclass


@dataclass
class DemandModel:
    """Demand probability model."""

    base_demand: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    noise: float
    min_demand: float
    max_demand: float

    def evaluate(self, price: float, size: float) -> float:
        price_norm = math.log10(max(1.0, price)) / math.log10(
            max(10.0, self.price_scale)
        )
        size_norm = math.log10(max(1.0, size)) / math.log10(max(10.0, self.size_scale))
        demand_penalty = (self.price_sensitivity * price_norm) + (
            self.size_sensitivity * size_norm
        )
        demand = self.base_demand * math.exp(-demand_penalty)
        demand *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_demand, min(self.max_demand, demand))