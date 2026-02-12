package config;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Config {

    private final String jsonContent;
    private final Path projectRoot;
    private final Path configPath;

    public Config() {
        
        try {
            String envRoot = System.getenv("PROJECT_ROOT");
            if (envRoot != null && !envRoot.isBlank()) {
                this.projectRoot = Paths.get(envRoot);
            } else {
                this.projectRoot = Paths.get("").toAbsolutePath();
            }

            this.configPath = projectRoot.resolve("config").resolve("config.json").normalize();
            if (!Files.exists(this.configPath)) {
                throw new RuntimeException("config.json not found at: " + this.configPath.toAbsolutePath());
            }

            this.jsonContent = Files.readString(this.configPath);
            
        } catch (IOException e) {
            throw new RuntimeException("Failed to load config.json", e);
        }
    }

    public Path getProjectRoot() {
        return projectRoot;
    }

    public Path getConfigDir() {
        Path dir = configPath.getParent();
        return (dir == null) ? configPath.toAbsolutePath().getParent() : dir;
    }

    public String getString(String section, String key) {
        // Regex to find "section": { ... } body
        Pattern sectionPattern = Pattern.compile("\"" + section + "\"\\s*:\\s*\\{([^}]+)\\}");
        Matcher sectionMatcher = sectionPattern.matcher(jsonContent);

        if (sectionMatcher.find()) {
            String sectionBody = sectionMatcher.group(1);
            // Regex to find "key": "value" within that body
            Pattern keyPattern = Pattern.compile("\"" + key + "\"\\s*:\\s*\"([^\"]+)\"");
            Matcher keyMatcher = keyPattern.matcher(sectionBody);
            if (keyMatcher.find()) {
                return keyMatcher.group(1);
            }
        }
        throw new IllegalArgumentException("Config key not found: " + section + "." + key);
    }
}
