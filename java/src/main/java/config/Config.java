package config;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class Config {

    private final JsonObject root;
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

            String jsonContent = Files.readString(this.configPath);
            this.root = JsonParser.parseString(jsonContent).getAsJsonObject();

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

    public JsonObject getRoot() {
        return root;
    }

    private JsonElement getElement(String... path) {
        JsonElement current = root;
        for (String key : path) {
            if (current == null || !current.isJsonObject()) {
                throw new IllegalArgumentException("Config path not found: " + String.join(".", path));
            }
            JsonObject obj = current.getAsJsonObject();
            current = obj.get(key);
        }
        if (current == null) {
            throw new IllegalArgumentException("Config path not found: " + String.join(".", path));
        }
        return current;
    }

    public JsonObject getObject(String... path) {
        return getElement(path).getAsJsonObject();
    }

    public JsonObject getObjectOrNull(String... path) {
        try {
            JsonElement element = getElement(path);
            return element != null && element.isJsonObject() ? element.getAsJsonObject() : null;
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    public JsonArray getArray(String... path) {
        return getElement(path).getAsJsonArray();
    }

    public JsonArray getArrayOrNull(String... path) {
        try {
            JsonElement element = getElement(path);
            return element != null && element.isJsonArray() ? element.getAsJsonArray() : null;
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    public String getString(String... path) {
        return getElement(path).getAsString();
    }

    public boolean getBoolean(String... path) {
        return getElement(path).getAsBoolean();
    }

    public double getDouble(String... path) {
        return getElement(path).getAsDouble();
    }

    public int getInt(String... path) {
        return getElement(path).getAsInt();
    }

    public String getString(String section, String key) {
        return getString(new String[]{section, key});
    }
}
