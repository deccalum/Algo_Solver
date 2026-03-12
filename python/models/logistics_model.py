import math

from dataclasses import dataclass


@dataclass
class LogisticsModel:
    """Logistics difficulty model."""

    min_size_log: float
    penalty_factor: float
    max_difficulty: float
    optimal: float
    base_cost: float

    def calculate_logistics(self, size: float) -> float:
        log_size = math.log10(max(self.min_size_log, size))
        log_opt = math.log10(max(self.min_size_log, self.optimal))
        diff = log_size - log_opt
        penalty = self.penalty_factor * (diff**2)
        val = self.base_cost + penalty
        return min(self.max_difficulty, val)