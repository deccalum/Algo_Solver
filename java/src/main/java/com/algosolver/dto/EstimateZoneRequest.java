package com.algosolver.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record EstimateZoneRequest(
        @NotBlank String mode,
        @NotNull Double spanShare,
        @NotNull Integer resolution,
        @NotNull Double step,
        @NotNull Double bias) {
}
