package com.algosolver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

import java.awt.Desktop;
import java.net.URI;

@SpringBootApplication
@ConfigurationPropertiesScan(basePackages = "com.algosolver.config")
public class Main {

    public static void main(String[] args) {
        SpringApplication.run(Main.class, args);
    }
}

@Component
class BrowserLauncher {
    private final Environment env;

    public BrowserLauncher(Environment env) {
        this.env = env;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void openBrowser() {
        String openBrowser = env.getProperty("app.open-browser", "true");
        if (!Boolean.parseBoolean(openBrowser)) {
            return;
        }

        String port = env.getProperty("server.port", "8080");
        String url = "http://localhost:" + port;

        System.out.println("\n" + "=".repeat(60));
        System.out.println("AlgoSolver is running");
        System.out.println("URL: " + url);
        System.out.println("=".repeat(60) + "\n");

        if (Desktop.isDesktopSupported()) {
            try {
                Desktop.getDesktop().browse(new URI(url));
            } catch (Exception e) {
                System.err.println("Could not open browser automatically: " + e.getMessage());
                System.out.println("Please open " + url + " manually");
            }
        }
    }
}