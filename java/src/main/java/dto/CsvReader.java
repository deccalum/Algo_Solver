package dto;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class CsvReader {

    private final FileImporter importer;

    public CsvReader() {
        this.importer = new FileImporter();
    }

    public List<DynamicModel> read(String fileKey) throws IOException {
        Path path = importer.getPath(fileKey);
        if (!Files.exists(path)) {
            throw new IOException("File not found: " + path);
        }

        List<String> lines = Files.readAllLines(path);
        if (lines.isEmpty()) {
            return new ArrayList<>();
        }

        // 1. Parse Headers from the first line
        String[] headers = lines.get(0).split(",");
        // Trim headers to remove whitespace
        for (int i = 0; i < headers.length; i++) {
            headers[i] = headers[i].trim();
        }

        List<DynamicModel> models = new ArrayList<>();

        // 2. Parse Data Rows
        for (int i = 1; i < lines.size(); i++) {
            String line = lines.get(i);
            if (line.trim().isEmpty()) {
                continue;
            }

            String[] values = line.split(",", -1); // -1 to keep empty trailing fields
            DynamicModel model = new DynamicModel();

            for (int h = 0; h < headers.length; h++) {
                String value = (h < values.length) ? values[h].trim() : "";
                model.set(headers[h], value);
            }
            models.add(model);
        }
        return models;
    }
}
