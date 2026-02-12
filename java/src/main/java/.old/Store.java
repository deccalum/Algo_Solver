
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class Store {
    private String name;
    private static double budget;
    private static int storeStaff;
    // private static double profit;
    private static Warehouse warehouse;
    private Generators.Store size;

    private double loans = 0.0; // track borrowed funds

    public int wage;
    // private double rent;
    private static double utilities;

    public Store() {
        Generators.Store s = Generators.randomStoreSize();
        double b = Generators.storeBudget(s);

        this.name = Generators.storeName();
        this.size = s;
        budget = b;

        Generators.Warehouse wSize = Generators.deriveWarehouseSize(s);
        warehouse = new Warehouse(wSize);

        storeStaff = Generators.storeEmployees(s);
        utilities = Generators.utilities(wSize);

        this.purchaseInitialInventory();
    }

    public Store(Generators.Store size) {
        this(size, Generators.storeBudget(size));
    }

    public Store(Generators.Store size, double budget) {
        this.name = Generators.storeName();
        this.size = size;

        Generators.Warehouse wSize = Generators.deriveWarehouseSize(size);
        warehouse = new Warehouse(wSize);

        storeStaff = Generators.storeEmployees(size);
        utilities = Generators.utilities(wSize);

        this.purchaseInitialInventory();
    }

    /**
     * Restock low inventory monthly with a profitability target to cover monthly spending.
     */
    public void restockLowStockMonthly() {
        Map<Product, Integer> inventory = warehouse.getInventory();
        double monthlyExpenses = getSpending();

        // Rank products by unit margin and restock until projected gross profit meets expenses
        java.util.List<Map.Entry<Product, Integer>> ranked = inventory.entrySet().stream()
            .sorted((a, b) -> Double.compare(
                unitMargin(b.getKey()), unitMargin(a.getKey())))
            .toList();

        double projectedGross = 0.0;
        // double restockCost = 0.0;

        for (Map.Entry<Product, Integer> entry : ranked) {
            if (projectedGross >= monthlyExpenses) break;
            Product product = entry.getKey();
            int current = entry.getValue();
            int threshold = 5;
            int target = 20;
            if (current >= threshold) continue;
            int qtyToOrder = Math.max(0, target - current);
            if (qtyToOrder == 0) continue;

            double unitMargin = unitMargin(product);
            double cost = product.getPrice() * qtyToOrder;

            if (!warehouse.hasSpaceFor(product, qtyToOrder)) continue;

            ensureBudget(cost);
            warehouse.addStock(product, qtyToOrder);
            budget -= cost;
            // restockCost += cost;
            projectedGross += unitMargin * qtyToOrder;
        }

        if (projectedGross < monthlyExpenses) {
            // Final safety: take loan to cover remaining gap explicitly
            double gap = monthlyExpenses - projectedGross;
            if (gap > 0) {
                takeLoan(gap);
            }
        }
    }

    /**
     * Borrow money to cover expenses when budget is insufficient.
     */
    public void takeLoan(double amount) {
        if (amount <= 0) return;
        loans += amount;
        budget += amount;
    }

    private void ensureBudget(double required) {
        if (budget < required) {
            takeLoan(required - budget);
        }
    }

    private double unitMargin(Product p) {
        return p.getRetailPrice() - p.getPrice();
    }
    
    private void purchaseInitialInventory() {
        // Generate available products from all categories
        List<Product> availableProducts = generateAvailableProducts(50); // 50 different products to choose from
        
        // Get recommended order from InventoryPlanner
        Map<Product, Integer> order = InventoryPlanner.suggestInitialOrder(this, availableProducts);
        
        // Add to warehouse
        for (Map.Entry<Product, Integer> entry : order.entrySet()) {
            warehouse.addStock(entry.getKey(), entry.getValue());
            System.out.println("Ordered: " + entry.getValue() + "x " + entry.getKey().getProductID());
        }
        
        // Deduct budget
        double totalCost = order.entrySet().stream()
            .mapToDouble(e -> e.getKey().getPrice() * e.getValue())
            .sum();
        budget -= totalCost;
        
        System.out.println("Initial inventory purchased for $" + String.format("%.2f", totalCost));
        System.out.println("Remaining budget: $" + String.format("%.2f", budget));
    }
    
    private List<Product> generateAvailableProducts(int count) {
        List<Product> products = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            products.add(new Product().generateProduct());
        }
        return products;
    }

    public static double spending() {
        double storewages = storeStaff * Generators.storeWage();
        double warehousewage = warehouse.getStaffCount() * Generators.warehouseWage();
        double warehouseRent = warehouse.getRent();

        return storewages + warehousewage + warehouseRent + utilities;
    }

    public static double profit() {
        return budget - spending();
    }

    public double getLoans() {
        return loans;
    }

    public double availableBudget() {
        return budget - spending();
    }

    public Generators.Store getSize() { return size; }
    public Warehouse getWarehouse() { return warehouse; }
    public String getName() { return name; }
    public double budget() { return budget; }
    public int storeStaff() { return storeStaff; }
    public double getSpending() { return spending(); }
}