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
        List<Product> products = generateProducts(10);
        System.out.println("=== INITIAL PRODUCTS ===");
        System.out.println(String.format("%-15s %-20s %-15s %-10s %-10s %-10s %-6s", 
                "PRODUCT ID", "NAME", "CATEGORY", "PRICE", "SIZE", "WEIGHT", "STOCK"));
        products.forEach(System.out::println);
        System.out.println();

        final int ORDER_GENERATION_INTERVAL_SECONDS = 5; // Generate order every 5 seconds

        while (simulationRunning && hasStock(products)) {
            try {
                // Adjust sleep based on speed multiplier
                LocalDateTime now = timeSimulator.getCurrentSimTime();
                Thread.sleep((long) (ORDER_GENERATION_INTERVAL_SECONDS * 1000 / timeSimulator.getSpeedMultiplier()));

                // Generate customer and order
                Customer customer = Customer.generateCustomer();
                Order order = createOrder(customer, products, now);

                if (order != null) {
                    System.out.println(">>> New order generated <<<");
                    System.out.println(order);
                    System.out.println(customer);

                    // Process order
                    orderProcessor.processOrder(order);
                    monthlyReport.recordOrder(order);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        System.out.println("Order generation stopped. No more stock available.");
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
            System.out.println("\nCommands: realtime | 4x | 8x | 32x | report | queue | quit");
            
            while (simulationRunning) {
                try {
                    System.out.print("> ");
                    String command = scanner.nextLine().trim().toLowerCase();
                    
                    switch (command) {
                        case "realtime" -> timeSimulator.setSpeed(1);
                        case "4x" -> timeSimulator.setSpeed(4);
                        case "8x" -> timeSimulator.setSpeed(8);
                        case "32x" -> timeSimulator.setSpeed(32);
                        case "report" -> {
                            LocalDateTime now = timeSimulator.getCurrentSimTime();
                            System.out.println(monthlyReport.generateReport(now));
                        }
                        case "queue" -> System.out.println("Orders in queue: " + businessHours.getQueueSize());
                        case "time" -> System.out.println("Current simulated time: " + timeSimulator.getCurrentSimTime());
                        case "quit" -> {
                            simulationRunning = false;
                            System.out.println("Shutting down simulation...");
                        }
                        default -> System.out.println("Unknown command. Try: realtime | 4x | 8x | 32x | report | queue | time | quit");
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

    private List<Product> generateProducts(int count) {
        List<Product> products = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            products.add(new Product().generateProduct());
        }
        return products;
    }

    private boolean hasStock(List<Product> products) {
        return products.stream().anyMatch(p -> p.getStock() > 0);
    }
}

