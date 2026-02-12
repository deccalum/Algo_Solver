
import java.util.concurrent.ConcurrentLinkedQueue;

public class BusinessHours {
    public static final int OPEN_HOUR = 9;  // 9 AM
    public static final int CLOSE_HOUR = 17; // 5 PM
    
    private final ConcurrentLinkedQueue<Order> orderQueue = new ConcurrentLinkedQueue<>();

    public static boolean withinBusinessHours(int hour) {
        return hour >= OPEN_HOUR && hour < CLOSE_HOUR;
    }

    public void queueOrder(Order order) {
        orderQueue.add(order);
    }

    public void processQueuedOrders(OrderProcessor processor) {
        if (!orderQueue.isEmpty()) {
            Order order;
            while ((order = orderQueue.poll()) != null) {
                processor.processOrder(order);
            }
        }
    }

    public int getQueueSize() {
        return orderQueue.size();
    }
}
