package com.algosolver.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {

    @GetMapping("/api")
    public Map<String, Object> home() {
        return Map.of(
                "status", "ok",
                "message", "Welcome to AlgoSolver API");
    }
}
