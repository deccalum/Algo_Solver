package com.algosolver.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record EstimateProductsRequest(
        @NotNull Double priceMin,
        @NotNull Double priceMax,
        @NotNull Double sizeMin,
        @NotNull Double sizeMax,
        @NotEmpty List<@Valid EstimateZoneRequest> priceZones,
        @NotEmpty List<@Valid EstimateZoneRequest> sizeZones) {
}
