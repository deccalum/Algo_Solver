
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class Order {
    final String id;
    private final Customer customer;
    private final List<OrderItem> items;
    private final LocalDateTime orderTimeStamp;
    private final int totalSize;
    private final int totalWeight;
    private final int shipping;
    private final double subTotal;

    public Order(Customer customer, List<OrderItem> items, LocalDateTime orderTimeStamp) {
        this.id = "ORD-" + UUID.randomUUID().toString().substring(0, 8);
        this.customer = customer;
        this.items = new ArrayList<>(items);
        this.orderTimeStamp = orderTimeStamp;

        this.totalSize = items.stream().mapToInt(OrderItem::getSize).sum();
        this.totalWeight = items.stream().mapToInt(OrderItem::getWeight).sum();

        this.shipping = (int) Math.ceil(this.totalWeight / 1000.0) * 5;
        
        this.subTotal = items.stream().mapToDouble(OrderItem::getSubtotal).sum();
    }

    public String getid() {
        return id;
    }
    public Customer getCustomer() {
        return customer;
    }
    public List<OrderItem> getItems() {
        return new ArrayList<>(items);
    }
    public double getTotal() {
        return subTotal + getShipping();
    }
    public LocalDateTime getOrderTimeStamp() {
        return orderTimeStamp;
    }
    public int getSize() {
        return totalSize;
    }
    public int getWeight() {
        return totalWeight;
    }
    public int getShipping() {
        if (shipping == 0) {
            return 5; // Minimum shipping cost
        }
        if (subTotal > 500) {
            return 0; // Free shipping for orders over $500
        }
        return shipping;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd MMM HH:mm");
        sb.append(String.format("%-14s %-20s\n", id, orderTimeStamp.format(formatter)));
        sb.append(String.format("%-4s %-25s %-15s %-12s %-12s %-15s\n", "QT", "Product", "Category", "Unit", "SubTotal", "Packaging"));
        for (OrderItem item : items) {
            sb.append(String.format(java.util.Locale.US, "%-4d %-25s %-15s $%-11.2f $%-11.2f %-15s\n",
                    item.getQuantity(),
                    item.getProduct().getName()[0] + " " + item.getProduct().getName()[1],
                    item.getProduct().getCategory(),
                    item.getProduct().getRetailPrice(),
                    item.getSubtotal(),
                    item.getProduct().getSize() + "cm/" + item.getProduct().getWeight() + "g"));
        }
        sb.append(String.format("\nTotal Size: %dcm, Total Weight: %dg\n", totalSize, totalWeight));
        sb.append(String.format("Shipping Cost: $%d\n", getShipping()));
        sb.append(String.format(java.util.Locale.US, "TOTAL AMOUNT: $%.2f\n", getTotal()));

        return sb.toString();
    }
}