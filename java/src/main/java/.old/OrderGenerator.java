
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Handles the automatic generation of customer orders during simulation
 */
public class OrderGenerator implements IOrderGenerator {
    private final Store store;
    private final TimeSimulator timeSimulator;
    private final OrderProcessor orderProcessor;
    private final MonthlyReport monthlyReport;
    private final Random random;
    
    private boolean generating = false;
    private Thread generatorThread;
    
    public OrderGenerator(Store store, TimeSimulator timeSimulator, 
                         OrderProcessor orderProcessor, MonthlyReport monthlyReport) {
        this.store = store;
        this.timeSimulator = timeSimulator;
        this.orderProcessor = orderProcessor;
        this.monthlyReport = monthlyReport;
        this.random = new Random();
    }
    
    @Override
    public void startGenerating() {
        if (generating) {
            return;
        }
        
        generating = true;
        generatorThread = new Thread(this::generateOrders);
        generatorThread.start();
    }
    
    @Override
    public void stopGenerating() {
        generating = false;
        if (generatorThread != null) {
            generatorThread.interrupt();
        }
    }
    
    @Override
    public boolean isGenerating() {
        return generating;
    }
    
    private void generateOrders() {
        // Compute a demand-targeted interval so we don't blow through stock on day one.
        int orderIntervalMinutes = computeDemandAwareIntervalMinutes();

        while (generating) {
            try {
                // Calculate sleep time: (minutes * ms_per_minute) / speed
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
                    continue; 
                }

                Customer customer = Customer.generateCustomer();
                Order order = createOrder(customer, available, now);

                if (order != null) {
                    orderProcessor.processOrder(order);
                    monthlyReport.recordOrder(order);
                    Log.logOrder(order);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        System.out.println("Order generation stopped.");
    }
    
    private Order createOrder(Customer customer, List<Product> availableProducts, LocalDateTime orderTime) {
        List<OrderItem> orderItems = new ArrayList<>();
        List<Product> inStock = availableProducts.stream()
                .filter(p -> p.getStock() > 0)
                .toList();

        if (inStock.isEmpty()) {
            return null;
        }

        int toBuy = random.nextInt(1, 3); // 1 to 2 products to slow depletion
        java.util.Map<Product, Integer> basket = new java.util.HashMap<>();

        for (int i = 0; i < toBuy; i++) {
            Product product = inStock.get(random.nextInt(inStock.size()));
            int available = store.getWarehouse().getStockLevel(product) - basket.getOrDefault(product, 0);
            if (available <= 0) {
                continue;
            }
            int quantity = random.nextInt(1, Math.min(2, available) + 1); // smaller per-line quantity
            basket.merge(product, quantity, Integer::sum);
        }

        basket.forEach((product, quantity) -> {
            // Only add if still in stock at the moment of order creation
            if (store.getWarehouse().getStockLevel(product) >= quantity) {
                orderItems.add(new OrderItem(product, quantity));
            }
        });

        return new Order(customer, orderItems, orderTime);
    }

    // Aim for revenue near monthly expenses by regulating order frequency.
    private int computeDemandAwareIntervalMinutes() {
        double monthlyExpenses = store.getSpending();
        double targetDailyRevenue = monthlyExpenses / 30.0;

        // Rough guess of average order value; use current inventory retail averages when possible
        double avgRetail = store.getWarehouse().getInventory().keySet().stream()
                .mapToDouble(Product::getRetailPrice)
                .average()
                .orElse(120.0);

        int targetOrdersPerDay = (int) Math.max(8, Math.ceil(targetDailyRevenue / avgRetail));
        // Clamp to avoid runaway order rates
        targetOrdersPerDay = Math.min(targetOrdersPerDay, 48); // at most every 30 minutes

        int minutesPerDay = 24 * 60;
        int interval = minutesPerDay / targetOrdersPerDay;

        // Also factor store size gently
        interval /= switch (store.getSize()) {
            case SMALL -> 1;
            case MEDIUM -> 2; // twice the demand
            case LARGE -> 3;  // triple the demand potential
        };

        // Keep interval reasonable (min 5 minutes simulated, max 120 minutes)
        interval = Math.max(5, Math.min(120, interval));
        return interval;
    }
}
