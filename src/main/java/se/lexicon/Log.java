package se.lexicon;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;

public class Log {
    static void purchase() {
        String fileName = "purchase_log.csv";
        // list?
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(fileName, true))) {
            
        } catch (IOException e) {
            System.err.println("Error writing to purchase log: " + e.getMessage());
        }
    }
    
    static void month() {
        String fileName = "monthly_report_log.csv";
        // list?
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(fileName, true))) {
            
        } catch (IOException e) {
            System.err.println("Error writing to monthly report log: " + e.getMessage());
        }
    }
}