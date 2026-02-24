package com.algosolver.config;

import org.springframework.boot.context.properties.bind.Name;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.List;

@ConfigurationProperties(prefix = "")
public record AppConfig(Path path, Solver solver, Generation generation) {
    public record Path(String dataOutput, String pythonSolver, String pythonGenerator) {
    }

    public record Solver(@Name("default") DefaultConfig defaults) {
        public record DefaultConfig(double budget, double space) {
        }
    }

    public record Generation(
            @Name("price_range") List<Double> priceRange,
            @Name("size_range") List<Double> sizeRange,
            @Name("logistics_optimal") double logisticsOptimal,
            @Name("logistics_base_cost") double logisticsBaseCost) {
    }
}