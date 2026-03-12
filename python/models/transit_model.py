import math

from dataclasses import dataclass

@dataclass
class TransitResult:
    mode:     str
    capacity: float
    cost:     float

@dataclass 
class TransitMode:
    name:                   str
    capacity:               float
    base_cost:              float
    max_value_density:      float
    min_weight_class:       float
    
@dataclass
class TransitModel:
    courier:                TransitMode
    pallet:                 TransitMode
    container:              TransitMode
    min_capacity_epsilon:   float
    weight_volume_ratio:    float
    origin:                 float

    def _apply_origin(self, cost: float, origin: float) -> float:
        capped = min(origin, self.origin)
        return cost * max(1.0, capped)

    def _total_cost(self, size: float, mode: TransitMode, origin: float) -> float:
        capacity = max(self.min_capacity_epsilon, mode.capacity)
        trips    = math.ceil(size / capacity)
        return self._apply_origin(trips * mode.base_cost, origin)

    def _is_eligible(self, mode: TransitMode, size: float, price: float) -> bool:
        value_density   = price / max(self.min_capacity_epsilon, size)
        estimated_weight = size * self.weight_volume_ratio
        return (
            value_density    <= mode.max_value_density and
            estimated_weight >= mode.min_weight_class
        )
    def assign_transit(
        self, size: float, price: float, origin_multiplier: float
    ) -> TransitResult:
        eligible = [m for m in (self.courier, self.pallet, self.container) if self._is_eligible(m, size, price)] or [self.pallet]

        best = min(eligible, key=lambda m: self._total_cost(size, m, origin_multiplier))
        return TransitResult(
            mode     = best.name,
            capacity = best.capacity,
            cost     = self._total_cost(size, best, origin_multiplier),
        )