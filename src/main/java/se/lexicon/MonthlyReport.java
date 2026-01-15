package se.lexicon;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MonthlyReport {
    private int totalOrders = 0;
    private double totalRevenue = 0.0;
    private final Map<Product, Integer> productSales = new HashMap<>();
    
    private final int currentMonth = -1;
    private final int currentYear = -1;

    public void recordOrder(Order order) {
        totalOrders++;
        totalRevenue += order.getTotal();
        
        // Track product sales
        for (OrderItem item : order.getItems()) {
            Product product = item.getProduct();
            int quantity = item.getQuantity();
            productSales.put(product, productSales.getOrDefault(product, 0) + quantity);
        }
    }

    public String generateReport(LocalDateTime monthEndDate) {
        StringBuilder report = new StringBuilder();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMMM yyyy");
        
        report.append("\n");
        report.append("=====================================\n");
        report.append("   MONTHLY SUMMARY REPORT\n");
        report.append("   ").append(monthEndDate.format(formatter)).append("\n");
        report.append("=====================================\n\n");
        
        // Revenue section
        report.append("REVENUE SUMMARY:\n");
        report.append("  Total Orders: ").append(totalOrders).append("\n");
        report.append(String.format("  Total Revenue: $%.2f\n", totalRevenue));
        
        if (totalOrders > 0) {
            double avgOrderValue = totalRevenue / totalOrders;
            report.append(String.format("  Average Order Value: $%.2f\n\n", avgOrderValue));
        } else {
            report.append("  Average Order Value: $0.00\n\n");
        }
        
        // Best sellers
        report.append("TOP 5 BEST SELLING PRODUCTS:\n");
        List<Map.Entry<Product, Integer>> sortedProducts = productSales.entrySet().stream()
                .sorted((a, b) -> b.getValue().compareTo(a.getValue()))
                .toList();
        
        for (int i = 0; i < Math.min(5, sortedProducts.size()); i++) {
            Map.Entry<Product, Integer> entry = sortedProducts.get(i);
            report.append(String.format("  %d. %s %s: %d units (Revenue: $%.2f)\n",
                    i + 1,
                    entry.getKey().getName()[0],
                    entry.getKey().getName()[1],
                    entry.getValue(),
                    entry.getKey().getPrice() * entry.getValue()));
        }
        
        report.append("\n");
        
        // Worst sellers
        report.append("TOP 5 LEAST SELLING PRODUCTS:\n");
        for (int i = Math.max(0, sortedProducts.size() - 5); i < sortedProducts.size(); i++) {
            Map.Entry<Product, Integer> entry = sortedProducts.get(i);
            int rank = sortedProducts.size() - i;
            report.append(String.format("  %d. %s %s: %d units (Revenue: $%.2f)\n",
                    rank - 4,
                    entry.getKey().getName()[0],
                    entry.getKey().getName()[1],
                    entry.getValue(),
                    entry.getKey().getPrice() * entry.getValue()));
        }
        
        report.append("\n");
        
        // Expenses section
        
        
        // Profit section
        report.append(String.format("NET PROFIT: $%.2f\n", Store.profit()));
        
        return report.toString();
    }

    public void resetMonthlyCounters() {
        totalOrders = 0;
        totalRevenue = 0.0;
        productSales.clear();
    }

    public int getTotalOrders() {
        return totalOrders;
    }

    public double getTotalRevenue() {
        return totalRevenue;
    }

    public Map<Product, Integer> getProductSales() {
        return new HashMap<>(productSales);
    }
}

/*

Enhance MonthlyReport:

warehouseCost = capacity_used * cost_per_m2
staffingCost = scales with warehouse size (small=1 person, large=10+)
inventoryCarryingCost = average_inventory_value * holding_rate
obsolescence_cost = products that don't sell
Methods:

calculateTotalOperatingCost() → salaries + warehouse + utilities + carrying
calculateROI(Product, soldQuantity) → return on investment per product
 */
