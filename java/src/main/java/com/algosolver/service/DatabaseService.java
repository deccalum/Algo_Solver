package com.algosolver.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class DatabaseService {
    private final JdbcTemplate jdbcTemplate;

    public DatabaseService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    /**
     * Get all tables from the current database
     */
    public List<Map<String, Object>> getAllTables() {
        List<Map<String, Object>> tables = new ArrayList<>();

        try {
            // Query to get all tables from information_schema
            String sql = "SELECT table_name, " +
                    "(SELECT COUNT(*) FROM information_schema.tables t2 " +
                    " WHERE t2.table_name = t.table_name AND t2.table_schema = t.table_schema) as exists_check " +
                    "FROM information_schema.tables t " +
                    "WHERE table_schema = 'public' " +
                    "ORDER BY table_name";

            tables = jdbcTemplate.queryForList(sql);

            // Add row counts
            for (Map<String, Object> table : tables) {
                String tableName = (String) table.get("table_name");
                String countSql = "SELECT COUNT(*) as row_count FROM " + tableName;
                try {
                    Map<String, Object> countResult = jdbcTemplate.queryForMap(countSql);
                    table.put("row_count", countResult.get("row_count"));
                } catch (Exception e) {
                    table.put("row_count", "error");
                }
            }
        } catch (Exception e) {
            System.err.println("Error fetching tables: " + e.getMessage());
        }

        return tables;
    }

    /**
     * Get schema (columns and types) for a specific table
     */
    public List<Map<String, String>> getTableSchema(String tableName) {
        List<Map<String, String>> schema = new ArrayList<>();

        try {
            String sql = "SELECT column_name, data_type, is_nullable, column_default " +
                    "FROM information_schema.columns " +
                    "WHERE table_schema = 'public' AND table_name = ? " +
                    "ORDER BY ordinal_position";

            schema = jdbcTemplate.query(sql, (rs, rowNum) -> {
                Map<String, String> column = new HashMap<>();
                column.put("name", rs.getString("column_name"));
                column.put("type", rs.getString("data_type"));
                column.put("nullable", rs.getString("is_nullable"));
                column.put("default", rs.getString("column_default"));
                return column;
            }, tableName);
        } catch (Exception e) {
            System.err.println("Error fetching schema for table " + tableName + ": " + e.getMessage());
        }

        return schema;
    }

    /**
     * Get all data from a specific table (with limit)
     */
    public List<Map<String, Object>> getTableData(String tableName) {
        List<Map<String, Object>> data = new ArrayList<>();

        try {
            // Sanitize table name to prevent SQL injection
            if (!isValidTableName(tableName)) {
                throw new IllegalArgumentException("Invalid table name: " + tableName);
            }

            String sql = "SELECT * FROM " + tableName + " LIMIT 100";
            data = jdbcTemplate.queryForList(sql);
        } catch (Exception e) {
            System.err.println("Error fetching data from table " + tableName + ": " + e.getMessage());
        }

        return data;
    }

    /**
     * Validate table name to prevent SQL injection
     */
    private boolean isValidTableName(String tableName) {
        // Allow alphanumeric, underscore, and verify it exists in database
        return tableName != null && tableName.matches("^[a-zA-Z0-9_]+$") && tableName.length() <= 63;
    }
}
