package com.algosolver.controller;

import com.algosolver.config.AppConfig;

import java.util.HashMap;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {

    private final AppConfig cfg;

    public HomeController(AppConfig cfg) {
        this.cfg = cfg;
    }

    @GetMapping("/api")
    public Map<String, Object> home() {
        return Map.of(
                "status", "ok",
                "message", "Welcome to AlgoSolver API");
    }

    @GetMapping("/api/config/bootstrap")
    public Map<String, Object> bootstrapConfig() {
        var solverDefaults = cfg != null && cfg.solver() != null ? cfg.solver().defaults() : null;
        var generation = cfg != null ? cfg.generation() : null;

        Map<String, Object> solver = new HashMap<>();
        solver.put("budget", solverDefaults != null ? solverDefaults.budget() : null);
        solver.put("space", solverDefaults != null ? solverDefaults.space() : null);

        Map<String, Object> generationMap = new HashMap<>();
        generationMap.put("priceRange", generation != null ? generation.priceRange() : null);
        generationMap.put("sizeRange", generation != null ? generation.sizeRange() : null);
        generationMap.put("logisticsOptimal", generation != null ? generation.logisticsOptimal() : null);
        generationMap.put("logisticsBaseCost", generation != null ? generation.logisticsBaseCost() : null);

        return Map.of(
                "solver", solver,
                "generation", generationMap);
    }
}
