package com.algosolver.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfigurationSource;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final CorsConfigurationSource corsConfigurationSource;

    public SecurityConfig(CorsConfigurationSource corsConfigurationSource) {
        this.corsConfigurationSource = corsConfigurationSource;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // Use CORS configuration
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                // Disable CSRF for API (stateless)
                .csrf(csrf -> csrf.disable())
                // Allow all requests without authentication in development
                .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())
                // Disable default login page
                .httpBasic(basic -> basic.disable());

        return http.build();
    }
}
