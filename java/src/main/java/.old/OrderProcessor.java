
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class OrderProcessor {
    private final ExecutorService executorService = Executors.newFixedThreadPool(10);
    private final ConcurrentHashMap<String, Future<?>> activeOrders = new ConcurrentHashMap<>();
    private final Random random = new Random();
    private final BusinessHours businessHours;

    public OrderProcessor(BusinessHours businessHours) {
        this.businessHours = businessHours;
    }

    public void processOrder(Order order) {
        Future<?> future = executorService.submit(() -> {
            int orderHour = order.getOrderTimeStamp().getHour();
            
            if (BusinessHours.withinBusinessHours(orderHour)) {
                // Process immediately
                executeOrder(order);
            } else {
                // Queue for later processing
                businessHours.queueOrder(order);
            }
        });
        
        activeOrders.put(order.getid(), future);
    }

    private void executeOrder(Order order) {
        try {
            // Simulate processing time (500-2000ms)
            int processingTime = random.nextInt(1500) + 500;
            Thread.sleep(processingTime);
            
            // Reduce stock for each item
            for (OrderItem item : order.getItems()) {
                item.getProduct().reduceStock(item.getQuantity());
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("Order processing interrupted: " + e.getMessage());
        } catch (IllegalArgumentException e) {
            System.err.println("Order " + order.getid() + " failed: " + e.getMessage());
        }
    }

    public void shutdown() {
        executorService.shutdown();
    }

    public boolean isProcessing(String orderId) {
        Future<?> future = activeOrders.get(orderId);
        return future != null && !future.isDone();
    }
}
