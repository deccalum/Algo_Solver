package config;

import java.nio.file.Path;

public class PathResolver {

    private final Config config;

    public PathResolver(Config config) {
        this.config = config;
    }

    /**
     * Resolves a named path from the config "system_paths" section. Uses
     * "data_output" as the base directory for other files.
     */
    public Path resolve(String fileKey) {
        // 1. Get the base output dir (e.g. "../data/output")
        String baseDirRaw = config.getString("system_paths", "data_output");

        // 2. Resolve base dir relative to the config directory
        Path baseDir = config.getConfigDir().resolve(baseDirRaw).normalize();

        // 3. Get the filename (e.g. "final_catalog.csv")
        String filename = config.getString("system_paths", fileKey);

        // 4. Combine
        return baseDir.resolve(filename).normalize();
    }
}
