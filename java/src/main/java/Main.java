
import java.io.IOException;
import java.time.LocalDate;
import java.util.List;

import config.Config;
import dto.CsvReader;
import dto.DynamicModel;
import model.World;
import service.PythonRunner;
import service.SimulationEngine;
import service.SimulationState;
import service.enums.Speed;
/**
 * 
 * @TODO: PythonRunner -> callable, configurable. Extract commands/args (edit
 * python scripts)
 * @TODO: Spending allocation. Able to eg. expand warehouse. In turn also return
 * a desired warehouse size or similar (would need a new solver that take
 * multiple warehouse sizes).
 * @TODO: Write compatible config values to java architecture instead 
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
                System.out.println("Running Python optimization...");
                int exitCode = runner.runScript("optimization_manager", List.of());
                if (exitCode != 0) {
                    System.err.println("Python script failed with exit code: " + exitCode);
                    return;
                }
                System.out.println("Python optimization completed successfully.");
            } catch (IOException | InterruptedException e) {
                System.err.println("Failed to run Python script: " + e.getMessage());
                return;
            }
        }


        CsvReader reader = new CsvReader();
        List<DynamicModel> items;
        try {
            items = reader.read("final_catalog_csv");
        } catch (IOException e) {
            return;
        }

        // Initialize simulation
        World world = new World();
        LocalDate startDate = LocalDate.now();

        SimulationState state = new SimulationState(startDate, world, null);

        System.out.println(startDate);
        SimulationEngine engine = new SimulationEngine(state);
        engine.setSpeed(Speed.X32);
        engine.start();
    }
}
