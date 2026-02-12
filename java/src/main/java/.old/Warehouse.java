
import java.util.HashMap;
import java.util.Map;

public class Warehouse {
    private int staff;
    private double rent;
    private int capacity;
    private int usedSpace;
    private String location;
    private Generators.Warehouse sizeBucket;

    // Inventory represented as a map of Product to quantity
    private Map<Product, Integer> stock = new HashMap<>();

    public Warehouse(Generators.Warehouse size) {
        this.sizeBucket = size;
        this.capacity = Generators.warehouseCapacity(size);
        this.usedSpace = 0;
        this.staff = Generators.warehouseEmployees(size);
        this.rent = Generators.rent(size);
        // location optional
    }

    public boolean hasSpaceFor(Product product, int quantity) {
        int requiredSpace = product.getSize() * quantity;
        return (usedSpace + requiredSpace) <= capacity;
    }

    public void addStock(Product product, int quantity) {
        if (!hasSpaceFor(product, quantity)) {
            throw new IllegalStateException("Not enough space in warehouse for product: " + product.getProductID());
        }
        stock.put(product, stock.getOrDefault(product, 0) + quantity);
        usedSpace += product.getSize() * quantity;

    }
    public void removeStock(Product product, int quantity) {
        Integer currentStock = stock.get(product);
        if (currentStock == null || currentStock < quantity) {
            throw new IllegalStateException("Insufficient stock for product: " + product.getProductID());
        }
        stock.put(product, currentStock - quantity);
        usedSpace -= product.getSize() * quantity;
    }

    public int getStockLevel(Product product) { return stock.getOrDefault(product, 0); }
    public double getRent() { return capacity * rent; }
    public int getCapacity() { return capacity - usedSpace; }
    public double getCapacityUtilization() { return ((double) usedSpace / capacity) * 100; }

    public void updateStaff(double handling) {
        int requiredStaff = (int) Math.ceil(handling / 1000); // 1 staff per 1000 handling units
        this.staff = Math.max(staff, requiredStaff);
    }

    public int getTotalCapacity() { return capacity; }
    public int getUsedCapacity() { return usedSpace; }
    public int getStaffCount() { return staff; }
    public String getLocation() { return location; }
    public Map<Product, Integer> getInventory() { return new HashMap<>(stock); }
    public Generators.Warehouse getSizeBucket() { return sizeBucket; }
}
