
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;

public class Log {
    private static final String SALES_LOG = "sales_log.csv";
    private static final String DAILY_LOG = "daily_log.csv";
    private static final String MONTHLY_LOG = "monthly_report_log.csv";

    static void logOrder(Order order) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(SALES_LOG, true))) {
            writer.write(String.format(
                "%s,%s,%.2f,%d\n",
                order.getid(),
                order.getOrderTimeStamp(),
                order.getTotal(),
                order.getItems().stream().mapToInt(OrderItem::getQuantity).sum()
            ));
        } catch (IOException e) {
            System.err.println("Error writing to sales log: " + e.getMessage());
        }
    }

    static void logDailySummary(String day, int orders, double revenue) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(DAILY_LOG, true))) {
            writer.write(String.format("%s,%d,%.2f\n", day, orders, revenue));
        } catch (IOException e) {
            System.err.println("Error writing to daily log: " + e.getMessage());
        }
    }

    static void logMonthlySummary(String monthLabel, String reportText) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(MONTHLY_LOG, true))) {
            writer.write("=== " + monthLabel + " ===\n");
            writer.write(reportText);
            writer.write("\n\n");
        } catch (IOException e) {
            System.err.println("Error writing to monthly report log: " + e.getMessage());
        }
    }

    static MonthTotals calculateMonthTotals(java.time.YearMonth month) {
        double revenue = 0.0;
        int orders = 0;
        java.nio.file.Path path = java.nio.file.Paths.get(SALES_LOG);
        if (!java.nio.file.Files.exists(path)) {
            return new MonthTotals(month, orders, revenue);
        }
        try {
            for (String line : java.nio.file.Files.readAllLines(path)) {
                String[] parts = line.split(",");
                if (parts.length < 3) continue;
                java.time.LocalDate lineDay = java.time.LocalDateTime.parse(parts[1]).toLocalDate();
                java.time.YearMonth ym = java.time.YearMonth.from(lineDay);
                if (ym.equals(month)) {
                    orders++;
                    revenue += Double.parseDouble(parts[2]);
                }
            }
        } catch (Exception e) {
            System.err.println("Error reading month totals: " + e.getMessage());
        }
        return new MonthTotals(month, orders, revenue);
    }

    static DayTotals calculateDayTotals(java.time.LocalDate day) {
        double revenue = 0.0;
        int orders = 0;
        java.nio.file.Path path = java.nio.file.Paths.get(SALES_LOG);
        if (!java.nio.file.Files.exists(path)) {
            return new DayTotals(day, orders, revenue);
        }
        try {
            for (String line : java.nio.file.Files.readAllLines(path)) {
                String[] parts = line.split(",");
                if (parts.length < 3) continue;
                java.time.LocalDate lineDay = java.time.LocalDateTime.parse(parts[1]).toLocalDate();
                if (lineDay.equals(day)) {
                    orders++;
                    revenue += Double.parseDouble(parts[2]);
                }
            }
        } catch (Exception e) {
            System.err.println("Error reading day totals: " + e.getMessage());
        }
        return new DayTotals(day, orders, revenue);
    }

    static String readLatestDailySummary() {
        return readLastLine(DAILY_LOG, "No daily log yet.");
    }

    static String readLatestMonthlySummary() {
        return readLastLine(MONTHLY_LOG, "No monthly log yet.");
    }

    private static String readLastLine(String fileName, String fallback) {
        try {
            java.nio.file.Path path = java.nio.file.Paths.get(fileName);
            if (!java.nio.file.Files.exists(path)) {
                return fallback;
            }
            java.util.List<String> lines = java.nio.file.Files.readAllLines(path);
            for (int i = lines.size() - 1; i >= 0; i--) {
                String line = lines.get(i).trim();
                if (!line.isEmpty()) {
                    return line;
                }
            }
            return fallback;
        } catch (IOException e) {
            return fallback;
        }
    }

    record DayTotals(java.time.LocalDate day, int orders, double revenue) {}
    record MonthTotals(java.time.YearMonth month, int orders, double revenue) {}
}