import math
import random

from dataclasses import dataclass


@dataclass
class StockModel:
    """Stock supply model."""

    base_stock: float
    min_stock: int
    noise: float
    infinite_stock_value: int
    infinite_chance_base: float
    infinite_decay_scale: float
    infinite_decay_size: float
    price_scale: float
    size_scale: float
    price_sensitivity: float
    size_sensitivity: float
    min_price_norm: float
    min_size_norm: float
    min_scale: float

    def generate_stock(self, price: float, size: float) -> int:
        chance_infinite = self.infinite_chance_base
        chance_infinite *= math.exp(-price / self.infinite_decay_scale)
        chance_infinite *= math.exp(
            -size / (self.infinite_decay_scale * self.infinite_decay_size)
        )
        chance_infinite = max(0.0, min(1.0, chance_infinite))

        if random.random() < chance_infinite:
            return self.infinite_stock_value

        price_norm = math.log10(max(self.min_price_norm, price)) / math.log10(
            max(self.min_scale, self.price_scale)
        )
        size_norm = math.log10(max(self.min_size_norm, size)) / math.log10(
            max(self.min_scale, self.size_scale)
        )
        stock_penalty = (self.price_sensitivity * price_norm) + (
            self.size_sensitivity * size_norm
        )
        stock = self.base_stock * math.exp(-stock_penalty)
        stock *= random.uniform(1.0 - self.noise, 1.0 + self.noise)
        return max(self.min_stock, int(stock))