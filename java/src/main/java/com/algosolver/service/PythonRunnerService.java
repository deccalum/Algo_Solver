package com.algosolver.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

@Service
public class PythonRunnerService {
    private final String pythonExecutable;
    private final String mainScript;

    public PythonRunnerService(
            @Value("${app.python.executable}") String pythonExecutable,
            @Value("${app.python.main-script}") String mainScript) {
        this.pythonExecutable = pythonExecutable;
        this.mainScript = mainScript;
    }

    public RunResult runGenerate() {
        List<String> command = new ArrayList<>();
        command.add(pythonExecutable);
        command.add(resolveMainScript().toString());

        try {
            ProcessBuilder processBuilder = new ProcessBuilder(command);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            String output;
            try (var input = process.getInputStream()) {
                output = new String(input.readAllBytes(), StandardCharsets.UTF_8);
            }

            int exitCode = process.waitFor();
            return new RunResult(exitCode, output);
        } catch (IOException ex) {
            throw new IllegalStateException("Failed to start python process", ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Python process interrupted", ex);
        }
    }

    private Path resolveMainScript() {
        Path userDir = Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        Path direct = userDir.resolve(mainScript).normalize();
        if (direct.toFile().exists()) {
            return direct;
        }
        throw new IllegalStateException("Cannot resolve python main script path: " + mainScript);
    }

    public record RunResult(int exitCode, String output) {
    }
}
