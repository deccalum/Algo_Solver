package com.algosolver.controller;

import com.algosolver.service.DatabaseService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/database")
public class DatabaseController {
    private final DatabaseService databaseService;

    public DatabaseController(DatabaseService databaseService) {
        this.databaseService = databaseService;
    }

    @GetMapping("/tables")
    public List<Map<String, Object>> getTables() {
        return databaseService.getAllTables();
    }

    @GetMapping("/tables/{tableName}/schema")
    public List<Map<String, String>> getTableSchema(@PathVariable String tableName) {
        return databaseService.getTableSchema(tableName);
    }

    @GetMapping("/tables/{tableName}/data")
    public List<Map<String, Object>> getTableData(@PathVariable String tableName) {
        return databaseService.getTableData(tableName);
    }
}
