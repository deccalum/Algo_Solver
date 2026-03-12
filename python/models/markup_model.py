import math
import random

from dataclasses import dataclass

@dataclass
class MarkupModel:
    """Markup model."""

    base_rate: float
    price_scale: float
    max_rate: float
    noise: float
    price_divisor: float
    min_rate: float
    max_rate_clamp: float

    def evaluate(self, price: float) -> float:
        price_factor = math.log10(max(1.0, price)) / self.price_divisor
        rate = self.base_rate + (price_factor * self.price_scale)
        rate = min(self.max_rate, max(self.min_rate, rate))
        rate *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_rate, min(self.max_rate_clamp, rate))