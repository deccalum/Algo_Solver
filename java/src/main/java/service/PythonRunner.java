package service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import config.Config;

public class PythonRunner {

    private final Config config;

    public PythonRunner(Config config) {
        this.config = config;
    }

    public boolean isEnabled() {
        JsonObject python = config.getObjectOrNull("python");
        if (python == null || !python.has("enabled")) {
            return false;
        }
        return python.get("enabled").getAsBoolean();
    }

    public int runScript(String scriptKey, List<String> extraArgs) throws IOException, InterruptedException {
        if (!isEnabled()) {
            return 0;
        }

        JsonObject python = config.getObject("python");
        String interpreter = python.has("interpreter")
                ? python.get("interpreter").getAsString()
                : "python";

        JsonObject scripts = python.getAsJsonObject("scripts");
        if (scripts == null || !scripts.has(scriptKey)) {
            throw new IllegalArgumentException("Missing python script key: " + scriptKey);
        }

        String scriptPathRaw = scripts.get(scriptKey).getAsString();
        Path scriptPath = config.getProjectRoot().resolve(scriptPathRaw).normalize();

        List<String> command = new ArrayList<>();
        command.add(interpreter);
        command.add(scriptPath.toString());

        JsonObject argsObj = python.has("args") ? python.getAsJsonObject("args") : null;
        if (argsObj != null && argsObj.has(scriptKey)) {
            JsonArray argsArray = argsObj.getAsJsonArray(scriptKey);
            for (JsonElement element : argsArray) {
                if (element.isJsonPrimitive()) {
                    command.add(element.getAsString());
                }
            }
        }

        if (extraArgs != null) {
            command.addAll(extraArgs);
        }

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.directory(config.getProjectRoot().toFile());
        builder.inheritIO();

        Process process = builder.start();
        return process.waitFor();
    }
}
