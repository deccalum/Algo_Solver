package com.algosolver.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.util.UriComponentsBuilder;
import java.util.*;

@RestController
@RequestMapping("/api/database")
public class DatabaseController {

    @Autowired
    private RestTemplate restTemplate;

    private static final String PYTHON_API_BASE = "http://127.0.0.1:18000/api";

    @GetMapping("/tables")
    public ResponseEntity<?> getTables() {
        try {
            return restTemplate.getForEntity(PYTHON_API_BASE + "/database/tables", List.class);
        } catch (Exception e) {
            return ResponseEntity.status(503)
                    .body(Map.of("error", "Python API unavailable", "details", e.getMessage()));
        }
    }

    @GetMapping("/tables/{tableName}/schema")
    public ResponseEntity<?> getTableSchema(@PathVariable String tableName) {
        try {
            return restTemplate.getForEntity(PYTHON_API_BASE + "/database/tables/" + tableName + "/schema", List.class);
        } catch (Exception e) {
            return ResponseEntity.status(503).body(Map.of("error", "Python API unavailable"));
        }
    }

    @GetMapping("/tables/{tableName}/data")
    public ResponseEntity<?> getTableData(
            @PathVariable String tableName,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "0") int offset,
            @RequestParam(required = false) String filters) {
        try {
            UriComponentsBuilder builder = UriComponentsBuilder
                    .fromUriString(PYTHON_API_BASE + "/database/tables/{tableName}/data")
                    .queryParam("limit", limit)
                    .queryParam("offset", offset);

            if (filters != null && !filters.isBlank()) {
                builder.queryParam("filters", filters);
            }

            String url = builder
                    .buildAndExpand(tableName)
                    .toUriString();

            return restTemplate.getForEntity(url, List.class);
        } catch (Exception e) {
            return ResponseEntity.status(503).body(Map.of("error", "Python API unavailable"));
        }
    }
}
