package se.lexicon;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class Store {
    private String name;
    private double budget;
    private int storeStaff;
    private Warehouse warehouse;
    private Generators.Store size;

    public int wage;
    private double rent;
    private double utilities;

    public Store() {
        Generators.Store s = Generators.randomStoreSize();
        double b = Generators.storeBudget(s);

        this.name = Generators.storeName();
        this.size = s;
        this.budget = b;

        Generators.Warehouse wSize = Generators.deriveWarehouseSize(s);
        this.warehouse = new Warehouse(wSize);

        this.storeStaff = Generators.storeEmployees(s);
        this.utilities = Generators.utilities(wSize);

        this.purchaseInitialInventory();
    }

    public Store(Generators.Store size) {
        this(size, Generators.storeBudget(size));
    }

    public Store(Generators.Store size, double budget) {
        this.name = Generators.storeName();
        this.size = size;
        this.budget = budget;

        Generators.Warehouse wSize = Generators.deriveWarehouseSize(size);
        this.warehouse = new Warehouse(wSize);

        this.storeStaff = Generators.storeEmployees(size);
        this.utilities = Generators.utilities(wSize);

        this.purchaseInitialInventory();
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
        this.budget -= totalCost;
        
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

    public double spending() {
        double storewages = storeStaff * Generators.storeWage();
        double warehousewage = warehouse.getStaffCount() * Generators.warehouseWage();
        double warehouseRent = warehouse.getRent();

        return storewages + warehousewage + warehouseRent + utilities;
    }

    public double availableBudget() {
        return budget - spending();
    }


    public Warehouse getWarehouse() { return warehouse; }
    public String getName() { return name; }
    public double budget() { return budget; }
    public int storeStaff() { return storeStaff; }
    public double getSpending() { return spending(); }
}

/*
public class InventoryPlanner {
    calculateOptimalOrder(StoreSize, budget, productList) → returns recommended purchases
    Logic:
    
    Filter products by profitability (high margin, fast velocity first)
    Check warehouse space constraints
    Bundle related products together
    Prioritize products that complement existing inventory
    Respect budget limit
    Consider reorder points (when to restock)
    Methods:
    
    rankProductsByProfitPerSquareMeter(List<Product>) → efficiency metric
    suggestInitialInventory(StoreSize, budget) → startup inventory
    suggestReorder(currentInventory, salesHistory) → replenishment logic
    optimizeForCashFlow(budget) → if low budget, prefer fast-movers
}
*/