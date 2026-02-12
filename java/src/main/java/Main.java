
import java.io.IOException;
import java.util.List;

import config.Config;
import dto.CsvReader;
import dto.DynamicModel;
import service.PythonRunner;

/**
 * Main class to demonstrate reading a CSV file and creating dynamic models.
 */
public class Main {

    public static void main(String[] args) {

        boolean skipPython = false;
        for (String arg : args) {
            if ("--skip-python".equalsIgnoreCase(arg)) {
                skipPython = true;
            }
        }

        Config config = new Config();
        PythonRunner runner = new PythonRunner(config);

        if (!skipPython && runner.isEnabled()) {
            try {
                int exitCode = runner.runScript("optimization_manager", List.of());
                if (exitCode != 0) {
                    System.err.println("Python script failed with exit code: " + exitCode);
                    return;
                }
            } catch (IOException | InterruptedException e) {
                System.err.println("Failed to run Python script: " + e.getMessage());
                return;
            }
        }

        // Read CSV and create dynamic models
        try {
            CsvReader reader = new CsvReader();

            List<DynamicModel> items = reader.read("final_catalog_csv");

            System.out.println("Loaded " + items.size() + " items.");

            if (!items.isEmpty()) {
                DynamicModel first = items.get(0);
                System.out.println("First Item Name: " + first.get("name"));
                System.out.println("Whole Model: " + first);
            }

        } catch (IOException e) {
            System.err.println("Failed to load CSV: " + e.getMessage());
        }
    }
}