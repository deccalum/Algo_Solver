
public class OrderItem {
    private final Product product;
    private final int quantity;
    private final double subtotal;
    private final int orderSize;
    private final int orderWeight;

    public OrderItem(Product product, int quantity) {
        this.product = product;
        this.quantity = quantity;
        this.subtotal = product.getRetailPrice() * quantity; // Use retail price for customers
        this.orderSize = product.getSize() * quantity;
        this.orderWeight = product.getWeight() * quantity;
    }

    public Product getProduct() {
        return product;
    }
    public int getQuantity() {
        return quantity;
    }
    public double getSubtotal() {
        return subtotal;
    }
    public int getSize() {
        return orderSize;
    }
    public int getWeight() {
        return orderWeight;
    }

    @Override
    public String toString() {
        return quantity + "x " + String.join(" ", product.getName()) +
                " @ $" + String.format("%.2f", product.getRetailPrice()) + " = $" + String.format("%.2f", subtotal);
    }
}