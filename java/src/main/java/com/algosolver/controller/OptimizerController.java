package com.algosolver.controller;

import com.algosolver.config.AppConfig;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/optimize")
public class OptimizerController {
    private final AppConfig cfg;

    public OptimizerController(AppConfig cfg) {
        this.cfg = cfg;
    }

    @PostMapping
    ResponseEntity<?> optimize() {
        return getScriptPath("solver")
            .map(this::runPythonScript)
            .orElseGet(() -> ResponseEntity.internalServerError().body(Map.of(
                "status", "ERROR",
                "message", "Missing config key: path.python_solver in app.yaml"
            )));
    }

    @PostMapping("/generate")
    ResponseEntity<?> generate() {
        return getScriptPath("generator")
            .map(this::runPythonScript)
            .orElseGet(() -> ResponseEntity.internalServerError().body(Map.of(
                "status", "ERROR",
                "message", "Missing config key: path.python_generator in app.yaml"
            )));
    }

    private Optional<String> getScriptPath(String scriptType) {
        if (cfg == null || cfg.path() == null) {
            return Optional.empty();
        }
        String scriptPath = switch (scriptType) {
            case "solver" -> cfg.path().pythonSolver();
            case "generator" -> cfg.path().pythonGenerator();
            default -> null;
        };
        if (scriptPath == null || scriptPath.isBlank()) {
            return Optional.empty();
        }
        return Optional.of(scriptPath);
    }

    private ResponseEntity<?> runPythonScript(String scriptPath) {
        try {
            ProcessBuilder pb = new ProcessBuilder("python", scriptPath);
            pb.redirectErrorStream(true);

            Process p = pb.start();
            String output;
            try (var in = p.getInputStream()) {
                output = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            }
            int exit = p.waitFor();

            if (exit != 0) {
                return ResponseEntity.internalServerError()
                    .body(Map.of("status", "ERROR", "exitCode", exit, "output", output));
            }
            return ResponseEntity.ok(Map.of("status", "OK", "output", output));
        } catch (Exception e) {
            return ResponseEntity.internalServerError()
                .body(Map.of("status", "ERROR", "message", e.getMessage()));
        }
    }
}