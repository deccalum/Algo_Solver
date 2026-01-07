package se.lexicon;

import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class InventoryPlanner {
    private static final double BASE_SALARY = Generators.warehouseWage();
    private static final double HANDLING_HOURS = 160; // hours/month
    

    //Suggests optimal initial inventory based on store budget and warehouse capacity
    public static Map<Product, Integer> suggestInitialOrder(Store store, List<Product> availableProducts) {
        Warehouse warehouse = store.getWarehouse();
        double availableBudget = store.budget();
        int availableSpace = warehouse.getTotalCapacity();
        
        // Rank products by profitability
        List<ProductScore> rankedProducts = rankProductsByProfit(availableProducts);
        
        // Build order iteratively
        Map<Product, Integer> order = new HashMap<>();
        double remainingBudget = availableBudget;
        int remainingSpace = availableSpace;
        
        for (ProductScore scored : rankedProducts) {
            Product product = scored.product;
            
            // Calculate max quantity constrained by budget, space, and demand
            int maxByBudget = (int) (remainingBudget / product.getPrice());
            int maxBySpace = remainingSpace / product.getSize();
            int maxByDemand = (int) (scored.estimatedDemand * 1.5); // 50% buffer
            
            int quantity = Math.min(Math.min(maxByBudget, maxBySpace), maxByDemand);
            
            if (quantity > 0) {
                order.put(product, quantity);
                
                // Deduct costs
                remainingBudget -= quantity * product.getPrice();
                remainingSpace -= quantity * product.getSize();
                
                // Recalculate staffing needs
                double totalHandling = calculateTotalHandling(order);
                int requiredStaff = (int) Math.ceil(totalHandling / HANDLING_HOURS);
                double staffingCost = requiredStaff * BASE_SALARY;
                
                // Adjust budget for additional staffing
                remainingBudget = availableBudget - staffingCost;
                
                // Stop if budget exhausted
                if (remainingBudget <= 0) break;
            }
        }
        
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