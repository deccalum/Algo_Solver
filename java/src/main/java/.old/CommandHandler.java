
import java.time.LocalDateTime;
import java.util.Scanner;

/**
 * Handles user input commands to control the simulation
 */
public class CommandHandler implements ICommandHandler {
    private final TimeSimulator timeSimulator;
    private final BusinessHours businessHours;
    private final MonthlyReport monthlyReport;
    
    private boolean running = true;
    
    public CommandHandler(TimeSimulator timeSimulator, BusinessHours businessHours, 
                         MonthlyReport monthlyReport) {
        this.timeSimulator = timeSimulator;
        this.businessHours = businessHours;
        this.monthlyReport = monthlyReport;
    }
    
    @Override
    public void handleCommands() {
        try (Scanner scanner = new Scanner(System.in)) {
            System.out.println("\nCommands: realtime | 4x | 8x | 32x | turbo (720x) | report | queue | time | quit");
            
            while (running) {
                try {
                    System.out.print("> ");
                    String command = scanner.nextLine().trim().toLowerCase();
                    
                    switch (command) {
                        case "realtime" -> {
                            timeSimulator.setSpeed(1);
                            System.out.println("Speed set to Real-time (1x)");
                        }
                        case "4x" -> {
                            timeSimulator.setSpeed(4);
                            System.out.println("Speed set to 4x");
                        }
                        case "8x" -> {
                            timeSimulator.setSpeed(8);
                            System.out.println("Speed set to 8x");
                        }
                        case "32x" -> {
                            timeSimulator.setSpeed(32);
                            System.out.println("Speed set to 32x");
                        }
                        case "turbo" -> {
                            timeSimulator.setSpeed(720);
                            System.out.println("Speed set to Turbo (720x)");
                        }
                        case "report" -> {
                            LocalDateTime now = timeSimulator.getCurrentSimTime();
                            System.out.println(monthlyReport.generateReport(now));
                        }
                        case "queue" -> {
                            System.out.println("Orders in queue: " + businessHours.getQueueSize());
                        }
                        case "time" -> {
                            System.out.println("Current simulated time: " + timeSimulator.getCurrentSimTime());
                        }
                        case "quit" -> {
                            running = false;
                            System.out.println("Shutting down simulation...");
                        }
                        default -> {
                            System.out.println("Unknown command. Try: realtime | 4x | 8x | 32x | turbo | report | queue | time | quit");
                        }
                    }
                } catch (Exception e) {
                    System.err.println("Error: " + e.getMessage());
                }
            }
        }
    }
    
    @Override
    public void stop() {
        running = false;
    }
    
    public boolean isRunning() {
        return running;
    }
}
