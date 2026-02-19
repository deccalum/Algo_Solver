package com.algosolver.config;

import org.springframework.boot.context.properties.bind.Name;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "")
public record AppConfig(Path path, Solver solver) {
    public record Path(String dataOutput, String pythonSolver, String pythonGenerator) {
    }

    public record Solver(@Name("default") DefaultConfig defaults) {
        public record DefaultConfig(double budget, double space) {
        }
    }
}