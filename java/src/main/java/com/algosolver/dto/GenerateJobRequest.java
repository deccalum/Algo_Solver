package com.algosolver.dto;

import jakarta.validation.constraints.NotNull;

public record GenerateJobRequest(
        @NotNull Long configId,
        @NotNull Integer version) {
}
