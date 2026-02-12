package dto;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import config.Config;
import config.PathResolver;

public class FileImporter {

    private final PathResolver pathResolver;

    public FileImporter() {

        /**
         * Initializes the PathResolver with the configuration.
         * The configuration contains mappings of file keys.
         * This allows us to use logical keys to refer to files instead of hardcoding paths throughout the codebase.
         * See Config.java for how the file keys are defined and mapped to actual file paths.
         */
        this.pathResolver = new PathResolver(new Config());
    }

    /**
     * Resolves the file key into a Path object.
     */
    public Path getPath(String fileKey) {
        return pathResolver.resolve(fileKey);
    }

    /**
     * Reads all lines from the file specified by the file key.
     * @param fileKey The key that identifies the file in the configuration.
     * @return A list of strings, each representing a line in the file.
     * @throws IOException If the file cannot be found or read.
     */
    public List<String> readLines(String fileKey) throws IOException {
        Path p = getPath(fileKey);
        if (!Files.exists(p)) {
            throw new IOException("File not found: " + p.toAbsolutePath());
        }
        return Files.readAllLines(p);
    }
}
