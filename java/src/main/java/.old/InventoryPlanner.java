
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;


/**
 * UPDATED INVENTORY MANAGER
 * 
 * Rank products profit per cubic meter
 * @param wholesale price
 * @param retail price
 * @param handling cost
 * @param size (cm³)
 * @param weight (g)
 * @param related product relations
 * @param estimate amount 
 * from: 
 * past sales data - not yet implemented
 * market trends - not yet implemented
 * seasonality - not yet implemented
 * competitor pricing - not yet implemented
 * 
 * @param shipping cost 
 * from:
 * crossing border - not yet implemented
 * distance - not yet implemented
 * speed - not yet implemented
 * fragility - not yet implemented
 * 
 * @param next months expected demand
 * @param availability
 * [stores can decide to prepurchase products that are not yet available but expected to be popular]
 * 
 * price * estimate = product total revenue
 * size * estimate = product total space used
 * storesize - product total space used = remaining space
 * 
 * sizemodifier + shipping
 * 
 * 
 * use loop for all possible scenarios. return best one.
 * [link to commands for user inputs]
 * 
 * estimate * retail && size && weight && shipping && next
 */












public class InventoryPlanner {

    private static final double LABOUR_HOURS = BusinessHours.CLOSE_HOUR - BusinessHours.OPEN_HOUR - 1;
    

    //Suggests optimal initial inventory based on store budget and warehouse capacity
    public static Map<Product, Integer> suggestInitialOrder(Store store, List<Product> availableProducts) {
        Warehouse warehouse = store.getWarehouse();
        double availableBudget = store.budget();
        int availableSpace = warehouse.getTotalCapacity();
        
            System.out.println("[INVENTORY PLANNER]");
            System.out.println("Total Budget Available: $" + String.format("%.2f", availableBudget));
            System.out.println("Warehouse Total Capacity: " + availableSpace + " m²" + " (" + store.getSize() + ")");
            System.out.println("Warehouse Salary: $" + (Generators.warehouseWage()));
            //System.out.println("Handling Hours per Month: " + LABOUR_HOURS);
            System.out.println("Product cap: " + availableProducts.size());
        
        // Rank products by profitability
        List<ProductScore> rankedProducts = rankProductsByProfit(availableProducts);
        
            System.out.println("\n[PRODUCT RANKING BY PROFITABILITY]");
            System.out.println("Products ranked by Profit Per m²:");
            for (int i = 0; i < Math.min(5, rankedProducts.size()); i++) {
                ProductScore ps = rankedProducts.get(i);
                System.out.println(String.format("  %d. %s - $%.2f/m², Demand: %d units/month",
                    i + 1,
                    ps.product.getName()[0] + " " + ps.product.getName()[1],
                    ps.profitPerM2,
                    ps.estimatedDemand));
            }
            System.out.println("  ... (showing top 5 of " + rankedProducts.size() + " total)");
        
        // Build order iteratively
        Map<Product, Integer> order = new HashMap<>();
        double remainingBudget = availableBudget;
        int remainingSpace = availableSpace;
            int productCount = 0;
        
            System.out.println("\n[ORDER BUILDING - ITERATIVE SELECTION]");
            System.out.println("-".repeat(80));
        
        for (ProductScore scored : rankedProducts) {
            Product product = scored.product;
                productCount++;
            
                System.out.println("\n[PRODUCT " + productCount + "] " + product.getName()[0] + " " + product.getName()[1]);
                System.out.println("  Product ID: " + product.getProductID());
                System.out.println("  Category: " + product.getCategory());
                System.out.println("  Unit Price: $" + String.format("%.2f", product.getPrice()));
                System.out.println("  Size per Unit: " + product.getSize() + " cm²");
                System.out.println("  Weight per Unit: " + product.getWeight() + " g");
            
            // Calculate max quantity constrained by budget, space, and demand
                System.out.println("\n  [CONSTRAINT CALCULATIONS]");
            
                // Max by budget
            int maxByBudget = (int) (remainingBudget / product.getPrice());
                System.out.println("  Max by Budget = Remaining Budget ÷ Unit Price");
                System.out.println("    = $" + String.format("%.2f", remainingBudget) + " ÷ $" + String.format("%.2f", product.getPrice()));
                System.out.println("    = " + maxByBudget + " units");
            
                // Max by space
            int maxBySpace = remainingSpace / product.getSize();
                System.out.println("  Max by Space = Remaining Space ÷ Size per Unit");
                System.out.println("    = " + remainingSpace + " m² ÷ " + product.getSize() + " cm²");
                System.out.println("    = " + maxBySpace + " units");
            
                // Max by demand
            int maxByDemand = (int) (scored.estimatedDemand * 1.5); // 50% buffer
                System.out.println("  Max by Demand = Estimated Demand × 1.5 (50% safety buffer)");
                System.out.println("    = " + scored.estimatedDemand + " × 1.5");
                System.out.println("    = " + maxByDemand + " units");
            
                // Final quantity
            int quantity = Math.min(Math.min(maxByBudget, maxBySpace), maxByDemand);
                System.out.println("\n  [FINAL QUANTITY SELECTION]");
                System.out.println("  Final Quantity = min(maxByBudget, maxBySpace, maxByDemand)");
                System.out.println("    = min(" + maxByBudget + ", " + maxBySpace + ", " + maxByDemand + ")");
                System.out.println("    = " + quantity + " units");
            
            if (quantity > 0) {
                order.put(product, quantity);
                
                    // Cost calculation
                    double productCost = quantity * product.getPrice();
                    System.out.println("\n  [ORDER COST]");
                    System.out.println("  Order Cost = Quantity × Unit Price");
                    System.out.println("    = " + quantity + " × $" + String.format("%.2f", product.getPrice()));
                    System.out.println("    = $" + String.format("%.2f", productCost));
                
                    // Space calculation
                    int spaceUsed = quantity * product.getSize();
                    System.out.println("\n  [SPACE USED]");
                    System.out.println("  Space Used = Quantity × Size per Unit");
                    System.out.println("    = " + quantity + " × " + product.getSize() + " m²");
                    System.out.println("    = " + spaceUsed + " m²");
                
                // Deduct costs
                    remainingSpace -= spaceUsed;
                
                // Recalculate staffing needs
                double totalHandling = calculateTotalHandling(order);
                int requiredStaff = (int) Math.ceil(totalHandling / LABOUR_HOURS);
                double staffingCost = requiredStaff * Generators.warehouseWage();
                
                    System.out.println("\n  [STAFFING RECALCULATION]");
                    System.out.println("  Total Handling Cost = Sum of all product handling");
                    System.out.println("    = $" + String.format("%.2f", totalHandling));
                    System.out.println("  Required Staff = ceil(Total Handling ÷ Handling Hours)");
                    System.out.println("    = ceil($" + String.format("%.2f", totalHandling) + " ÷ " + LABOUR_HOURS + ")");
                    System.out.println("    = " + requiredStaff + " workers");
                    System.out.println("  Staffing Cost = Required Staff × Base Salary");
                    System.out.println("    = " + requiredStaff + " × $" + (Generators.warehouseWage()));
                    System.out.println("    = $" + String.format("%.2f", staffingCost));
                
                // Adjust budget for additional staffing
                remainingBudget = availableBudget - staffingCost;
                
                    System.out.println("\n  [BUDGET SUMMARY]");
                    System.out.println("  Remaining Budget = Total Budget - Staffing Cost");
                    System.out.println("    = $" + String.format("%.2f", availableBudget) + " - $" + String.format("%.2f", staffingCost));
                    System.out.println("    = $" + String.format("%.2f", remainingBudget));
                    System.out.println("  Remaining Space = " + remainingSpace + " m²");
                
                // Stop if budget exhausted
                    if (remainingBudget <= 0) {
                        System.out.println("\n  *** BUDGET EXHAUSTED - STOPPING INVENTORY SELECTION ***");
                        break;
                    }
                } else {
                    System.out.println("\n  *** SKIPPED: Quantity is 0 (insufficient budget/space/demand) ***");
            }
        }
        
            System.out.println("\n" + "-".repeat(80));
            System.out.println("[FINAL INVENTORY ORDER SUMMARY]");
            System.out.println("Total Products Selected: " + order.size());
            double totalOrderCost = order.entrySet().stream()
                .mapToDouble(e -> e.getKey().getPrice() * e.getValue())
                .sum();
            System.out.println("Total Order Cost: $" + String.format("%.2f", totalOrderCost));
            System.out.println("Total Budget Used: $" + String.format("%.2f", availableBudget - remainingBudget));
            System.out.println("Final Remaining Budget: $" + String.format("%.2f", remainingBudget));
            System.out.println("Final Remaining Space: " + remainingSpace + " m²");
            System.out.println("=".repeat(80) + "\n");
        
        return order;
    }
    
    // Ranks products by profit per square meter (efficiency metric)
    private static List<ProductScore> rankProductsByProfit(List<Product> products) {
        return products.stream()
            .map(p -> new ProductScore(p, estimateDemand(p), calculateProfitPerM2(p)))
            .sorted(Comparator.comparingDouble(ps -> -ps.profitPerM2)) // Descending
            .collect(Collectors.toList());
    }
    
    private static double calculateProfitPerM2(Product product) {
        double retailPrice = product.getPrice() * 1.5; // Assume 50% markup
        double handlingCost = Generators.productHandling(product.getWeight(), 0, product.getSize());
        double profit = retailPrice - product.getPrice() - handlingCost;
        double sizeInM2 = product.getSize() / 10000.0; // cm² to m²
        return profit / sizeInM2;
    }
    
    private static int estimateDemand(Product product) {
        // Simple demand estimation (can be enhanced later with trends/seasonality)
        String category = product.getCategory();
        return switch (category) {
            case "Audio", "Handhelds" -> 50 + (int)(Math.random() * 100); // 50-150 units/month
            case "Computers" -> 30 + (int)(Math.random() * 70);           // 30-100 units/month
            case "Wearables" -> 40 + (int)(Math.random() * 80);           // 40-120 units/month
            default -> 20 + (int)(Math.random() * 50);                    // 20-70 units/month
        };
    }
    
    private static double calculateTotalHandling(Map<Product, Integer> order) {
        return order.entrySet().stream()
            .mapToDouble(e -> {
                Product p = e.getKey();
                int qty = e.getValue();
                return Generators.productHandling(p.getWeight(), 0, p.getSize()) * qty;
            })
            .sum();
    }
    
    // Inner class to hold product scoring data
    private static class ProductScore {
        Product product;
        int estimatedDemand;
        double profitPerM2;
        
        ProductScore(Product product, int demand, double profit) {
            this.product = product;
            this.estimatedDemand = demand;
            this.profitPerM2 = profit;
        }
    }
}