package com.algosolver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Component;

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

        // New: allow opening frontend dev server if specified
        String openFrontendDev = env.getProperty("app.open-frontend-dev", "false");
        String url;
        if (Boolean.parseBoolean(openFrontendDev)) {
            url = "http://localhost:3000";
        } else {
            String port = env.getProperty("server.port", "8080");
            url = "http://localhost:" + port;
        }

        System.out.println("\n" + "=".repeat(60));
        System.out.println("AlgoSolver running");
        System.out.println("URL: " + url);
        System.out.println("=".repeat(60) + "\n");

        try {
            String os = System.getProperty("os.name").toLowerCase();
            ProcessBuilder pb;

            if (os.contains("win")) {
                // Windows: use cmd /c start
                pb = new ProcessBuilder("cmd", "/c", "start", url);
            } else if (os.contains("mac")) {
                // macOS: use open
                pb = new ProcessBuilder("open", url);
            } else {
                // Linux/Unix: use xdg-open
                pb = new ProcessBuilder("xdg-open", url);
            }

            pb.start();
        } catch (Exception e) {
            System.err.println("Could not open browser: " + e.getMessage());
            System.out.println("Please open " + url + " manually");
        }
    }
}