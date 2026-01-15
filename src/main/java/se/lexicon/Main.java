package se.lexicon;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.Scanner;

public class Main {
    private final TimeSimulator timeSimulator;
    private final Store store;
    private final OrderProcessor orderProcessor;
    private final BusinessHours businessHours;
    private final MonthlyReport monthlyReport;
    
    private boolean simulationRunning = true;
    private int previousMonth = -1;
    private final Random random = new Random();

    public Main() {
        this.store = new Store();
        this.businessHours = new BusinessHours();
        this.timeSimulator = new TimeSimulator();
        this.orderProcessor = new OrderProcessor(businessHours);
        this.monthlyReport = new MonthlyReport();
    }

    public static void main(String[] args) {
        Main simulator = new Main();
        simulator.start();
    }

    public void start() {
        System.out.println("Starting Shop Simulator: " + store.getName());
        System.out.println("Store Size: " + store.getSize());
        System.out.println("Initial Budget: $" + store.budget());

        
        // Initial speed 720x
        System.out.println("Setting simulation to Turbo Speed (720x) - 1 Month ≈ 1 Minute");
        timeSimulator.setSpeed(720);

        //Start time simulation
        Thread timeThread = new Thread(() -> timeSimulator.tick());
        timeThread.start();

        // Start order generation
        Thread orderThread = new Thread(this::generateOrders);
        orderThread.start();

        // Start month-end checking
        Thread monthCheckThread = new Thread(this::checkMonthEnd);
        monthCheckThread.start();

        // Start handling user commands (Blocks the main thread)
        handleUserCommands();

        // Cleanup
        timeSimulator.stop();
        orderProcessor.shutdown();
    }

    private void generateOrders() {
        // Determine order interval based on store size
        int orderIntervalMinutes = switch (store.getSize()) {
            case SMALL -> 60;  // 1 order every hour
            case MEDIUM -> 30; // 1 order every 30 mins
            case LARGE -> 10;  // 1 order every 10 mins
        };

        while (simulationRunning) {
            try {
                // Calculate sleep time: (minutes * ms_per_minute) / speed
                // 1 simulated minute = 1000ms / speed
                long sleepMs = (long) orderIntervalMinutes * 1000L / timeSimulator.getSpeedMultiplier();
                
                // Ensure we don't sleep 0 or negative
                if (sleepMs < 1) sleepMs = 1;
                
                Thread.sleep(sleepMs);

                LocalDateTime now = timeSimulator.getCurrentSimTime();
                
                // Get available products from warehouse
                List<Product> available = new ArrayList<>();
                var inventory = store.getWarehouse().getInventory();
                for (var entry : inventory.entrySet()) {
                    if (entry.getValue() > 0) {
                        available.add(entry.getKey());
                    }
                }

                if (available.isEmpty()) {
                    // System.out.println("DEBUG: No stock available to sell.");
                    continue; 
                }

                Customer customer = Customer.generateCustomer();
                Order order = createOrder(customer, available, now);

                if (order != null) {
                    System.out.println(">>> New order generated <<<");
                    System.out.println(order);
                    System.out.println(customer);

                    // Process order
                    orderProcessor.processOrder(order);
                    
                    // Deduct stock immediately to prevent selling same item twice before processor runs
                    // (Though OrderProcessor also does it, we should coordinate. 
                    // ideally createOrder claims the stock.)
                    // For now, let's just record it.
                    // Note: OrderProcessor.executeOrder reduces stock. 
                    // We need to ensure we don't sell what we don't have.
                    // The available list check helps, but concurrency is tricky.
                    
                    monthlyReport.recordOrder(order);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        System.out.println("Order generation stopped.");
    }

    private void checkMonthEnd() {
        while (simulationRunning) {
            try {
                Thread.sleep(1000); // Check every second
                
                if (timeSimulator.isMonthEnd()) {
                    LocalDateTime now = timeSimulator.getCurrentSimTime();
                    int currentMonth = now.getMonthValue();
                    
                    if (previousMonth != currentMonth) {
                        previousMonth = currentMonth;
                        
                        // Generate report
                        String report = monthlyReport.generateReport(now);
                        System.out.println(report);
                        
                        // Reset counters for next month
                        monthlyReport.resetMonthlyCounters();
                        
                        // Process any queued orders
                        businessHours.processQueuedOrders(orderProcessor);
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private void handleUserCommands() {
        try (Scanner scanner = new Scanner(System.in)) {
            System.out.println("\nCommands: realtime | 4x | 8x | 32x | turbo (720x) | report | queue | quit");
            
            while (simulationRunning) {
                try {
                    System.out.print("> ");
                    String command = scanner.nextLine().trim().toLowerCase();
                    
                    switch (command) {
                        case "realtime" -> timeSimulator.setSpeed(1);
                        case "4x" -> timeSimulator.setSpeed(4);
                        case "8x" -> timeSimulator.setSpeed(8);
                        case "32x" -> timeSimulator.setSpeed(32);
                        case "turbo" -> timeSimulator.setSpeed(720);
                        case "report" -> {
                            LocalDateTime now = timeSimulator.getCurrentSimTime();
                            System.out.println(monthlyReport.generateReport(now));
                        }
                        case "queue" -> System.out.println("Orders in queue: " + businessHours.getQueueSize());
                        case "time" -> System.out.println("Current simulated time: " + timeSimulator.getCurrentSimTime()); // #
                        case "quit" -> {
                            simulationRunning = false;
                            System.out.println("Shutting down simulation...");
                        }
                        default -> System.out.println("Unknown command. Try: realtime | 4x | 8x | 32x | turbo | report | queue | time | quit");
                    }
                } catch (Exception e) {
                    System.err.println("Error: " + e.getMessage());
                }
            }
        }
    }

    private Order createOrder(Customer customer, List<Product> availableProducts, LocalDateTime orderTime) {
        List<OrderItem> orderItems = new ArrayList<>();
        List<Product> inStock = availableProducts.stream()
                .filter(p -> p.getStock() > 0)
                .toList();

        if (inStock.isEmpty()) {
            return null;
        }

        int toBuy = random.nextInt(1, 5); // 1 to 4 products
        java.util.Map<Product, Integer> basket = new java.util.HashMap<>();

        for (int i = 0; i < toBuy; i++) {
            Product product = inStock.get(random.nextInt(inStock.size()));
            int quantity = random.nextInt(1, 4); // 1 to 3 units
            basket.merge(product, quantity, Integer::sum);
        }

        basket.forEach((product, quantity) -> {
            orderItems.add(new OrderItem(product, quantity));
        });

        return new Order(customer, orderItems, orderTime);
    }
}

