package com.algosolver;


import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;


@SpringBootApplication
@ConfigurationPropertiesScan(basePackages = "com.algosolver.config")
public class Main {

    static void main(String[] args) {
        SpringApplication.run(Main.class, args);
    }
}