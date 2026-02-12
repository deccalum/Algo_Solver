
import java.io.IOException;
import java.util.List;

import dto.CsvReader;
import dto.DynamicModel;

/**
 * Main class to demonstrate reading a CSV file and creating dynamic models.
 */
public class Main {

    public static void main(String[] args) {

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
        }
    }
}