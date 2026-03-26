package com.algosolver.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
public class CorsConfig {

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // Allow requests from localhost frontend servers
        configuration.setAllowedOrigins(Arrays.asList(
                "http://localhost:3000", // Vite dev server
                "http://localhost:5173", // Alternative Vite port
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"));

        // Allow common HTTP methods
        configuration.setAllowedMethods(Arrays.asList(
                "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));

        // Allow credentials (cookies, authorization headers)
        configuration.setAllowCredentials(true);

        // Allow custom headers
        configuration.setAllowedHeaders(Arrays.asList(
                "Content-Type",
                "Authorization",
                "Accept",
                "Origin"));

        // Expose response headers if needed
        configuration.setExposedHeaders(Arrays.asList(
                "Content-Type",
                "Authorization"));

        // Cache preflight requests for 1 hour
        configuration.setMaxAge(3600L);

        // Apply to all endpoints
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);

        return source;
    }
}
