
import java.util.Random;


/*
 * Comprehensive demand modifier system considering multiple market factors.
 * Returns a multiplier (e.g., 0.5 = 50% of base demand, 2.0 = 200% of base demand)
 * 
 * Factors included:
 * 1. Seasonal popularity (0.6 to 1.4)
 * 2. Product rating/handling quality (0.7 to 1.5)
 * 3. Competitor pricing advantage (0.6 to 1.5)
 * 4. New/popular product boost (1.0 to 1.4)
 * 5. Discount/promotion boost (1.0 to 1.6)
 * 6. Customer budget constraints (0.5 to 1.0)
 * 7. Random trend variation (0.8 to 1.2)
 */

public class DemandModifier {
    
    private static final Random random = new Random();
    
    /**
     * Main demand modifier calculation.
     * 
     * @param productType Type of product (e.g., "Handhelds", "Computers")
     * @param season Current season ("spring", "summer", "fall", "winter")
     * @param productRating Product rating 0-100 (based on handling, manufacturer, returns)
     * @param productPrice Our selling price
     * @param competitorPrice Competitor's price (can be 0 if unknown)
     * @param isNew Is this a new product?
     * @param discounted Is the product currently discounted?
     * @return Demand multiplier to apply to base demand
     */
    public static double calculateDemandModifier(Product product, String season, int productRating, double competitorPrice, boolean discounted) {

        double demandMultiplier = 1.0;
        
        // 1. SEASONAL POPULARITY MODIFIER (0.6 to 1.4)
        double seasonalMod = calculateSeasonalModifier(season, product.getCategory());
        demandMultiplier *= seasonalMod;
        
        // 2. PRODUCT RATING/HANDLING QUALITY MODIFIER (0.7 to 1.5)
        // Rating 0-100: 0 = poor handling, 100 = excellent handling
        double ratingMod = 0.7 + (productRating / 100.0) * 0.8; // 0.7 to 1.5
        demandMultiplier *= ratingMod;
        
        // 3. COMPETITOR PRICING MODIFIER (0.6 to 1.5)
        // If our price is lower than competitors, demand increases
        double pricingMod = calculateCompetitorPricingModifier(product.getRetailPrice(), competitorPrice);
        demandMultiplier *= pricingMod;
        
        // 4. NEW PRODUCT BOOST (1.0 to 1.4)
        if (product.isNew()) {
            demandMultiplier *= 1.35; // New products get significant boost
        }
        
        // 5. DISCOUNT/PROMOTION BOOST (1.0 to 1.6)
        if (discounted) {
            demandMultiplier *= 1.5; // Discounts significantly increase demand
        }
        
        // 6. CUSTOMER BUDGET CONSTRAINTS (0.5 to 1.0)
        // Exponential distribution: most customers have lower budgets
        // Higher price products face budget constraint penalty
        double budgetMod = calculateBudgetConstraintModifier(product.getRetailPrice());
        demandMultiplier *= budgetMod;
        
        // 7. RANDOM TREND VARIATION (0.8 to 1.2)
        // Accounts for unpredictable market shifts
        double trendVariation = 0.8 + (random.nextDouble() * 0.4);
        demandMultiplier *= trendVariation;
        
        return Math.round(demandMultiplier * 100.0) / 100.0; // Round to 2 decimals
    }
    
    /**
     * Calculates seasonal popularity modifier based on product type and season.
     * Different products peak in different seasons.
     * 
     * Returns: 0.6 to 1.4
     */
    private static double calculateSeasonalModifier(String season, String productType) {
        // Base seasonal effect (0.8 to 1.3)
        double seasonalBase = switch (season.toLowerCase()) {
            case "spring" -> 1.1;   // Spring refresh spending
            case "summer" -> 1.2;   // Summer peak season
            case "fall" -> 1.0;     // Back to school/work
            case "winter" -> 1.15;  // Holiday shopping
            default -> 1.0;
        };
        
        // Product-specific seasonal adjustments
        double productSeasonalBoost = switch (productType.toLowerCase()) {
            case "handhelds" -> seasonalBase + 0.1;     // Always popular
            case "audio" -> seasonalBase + 0.05;        // Consistent demand
            case "computers" -> 0.9 + (seasonalBase * 0.2); // Back to school peak
            case "wearables" -> seasonalBase;
            case "entertainment" -> seasonalBase * 1.15; // Holiday boost
            case "imaging" -> seasonalBase + 0.05;
            case "networking" -> 1.0; // Steady demand
            default -> seasonalBase;
        };
        
        return Math.max(0.6, Math.min(1.4, productSeasonalBoost)); // Clamp between 0.6 and 1.4
    }
    
    /**
     * Competitor pricing modifier: if our price is lower, demand increases.
     * Formula: 1.0 + (competitor_price - our_price) / our_price * adjustment_factor
     * 
     * Returns: 0.6 to 1.5
     */
    private static double calculateCompetitorPricingModifier(double ourPrice, double competitorPrice) {
        if (competitorPrice <= 0) return 1.0; // No data on competitor, neutral
        
        double priceDifference = (competitorPrice - ourPrice) / ourPrice;
        
        if (priceDifference > 0) {
            // We're cheaper: boost demand (max 1.5)
            return Math.min(1.5, 1.0 + (priceDifference * 0.8));
        } else {
            // We're more expensive: reduce demand (min 0.6)
            return Math.max(0.6, 1.0 + (priceDifference * 0.5));
        }
    }
    
    /**
     * Customer budget constraint modifier using exponential distribution.
     * Most customers have limited budgets; luxury items face penalties.
     * Assumes average customer budget is around $500.
     * 
     * Returns: 0.5 to 1.0
     */
    private static double calculateBudgetConstraintModifier(double productPrice) {
        double averageCustomerBudget = 500.0; // Assume avg customer budget
        double affordabilityRatio = productPrice / averageCustomerBudget;
        
        // Exponential decay: cheaper items = higher multiplier
        // Price of $500 = multiplier 1.0
        // Price of $250 = multiplier ~1.0
        // Price of $1000 = multiplier ~0.61
        double budgetMod = Math.exp(-0.5 * Math.max(0, affordabilityRatio - 1.0));
        
        return Math.max(0.5, Math.min(1.0, budgetMod)); // Clamp between 0.5 and 1.0
    }
    
    /**
     * Generates a realistic customer budget using exponential distribution.
     * Most customers have modest budgets; few have very high budgets.
     * 
     * Returns: Budget between $50 and $2000, with most under $500
     */
    public static double generateCustomerBudget() {
        // Exponential distribution with mean $300
        double lambda = 1.0 / 300.0;
        double u = random.nextDouble();
        double budget = -Math.log(1.0 - u) / lambda;
        
        // Cap at reasonable max ($2000)
        return Math.min(2000, Math.max(50, budget));
    }
    
    /**
     * Calculates product rating (0-100 scale) based on:
     * - Warehouse handling efficiency (wages, worker count)
     * - Manufacturer quality (base 60-90 by tier)
     * - Return rate (reduces rating)
     * 
     * 0-100 scale where:
     * 0-40 = Poor (high returns, cheap manufacturer)
     * 40-60 = Average
     * 60-80 = Good
     * 80-100 = Excellent
     */
    public static int calculateProductRating(double handlingQuality, double manufacturerQuality, double returnRate) {
        // Handling quality (0-100): higher wages/more workers = better handling
        double handlingScore = Math.min(100, Math.max(0, handlingQuality * 100.0));
        
        // Manufacturer quality (0-100): cheap manufacturers = lower score
        double mfgScore = Math.min(100, Math.max(0, manufacturerQuality * 100.0));
        
        // Return rate penalty (0-100): each 1% return reduces rating ~2 points
        double returnPenalty = Math.max(0, 100 - (returnRate * 200.0));
        
        // Weighted average: 40% handling, 40% manufacturer, 20% returns
        double rating = (handlingScore * 0.4) + (mfgScore * 0.4) + (returnPenalty * 0.2);
        
        return Math.max(0, Math.min(100, (int) rating));
    }
    
    /**
     * Determines manufacturer quality tier (0.6 to 1.2 multiplier).
     * Quality affects base rating and product reliability.
     * 
     * Cheap manufacturers (multiplier 0.6) produce faulty products more often
     * Premium manufacturers (multiplier 1.2) produce reliable products
     */
    public static double getManufacturerQuality(String manufacturerTier) {
        return switch (manufacturerTier.toLowerCase()) {
            case "budget" -> 0.6;      // Budget: 60% quality, higher returns
            case "standard" -> 0.85;   // Standard: 85% quality
            case "premium" -> 1.0;     // Premium: 100% quality baseline
            case "luxury" -> 1.15;     // Luxury: Enhanced quality
            default -> 0.85;
        };
    }
    
    /**
     * Calculates the effect of warehouse staffing efficiency on product handling.
     * - Low wages/few workers = poor handling (0.5)
     * - High wages/many workers = excellent handling (1.0)
     */
    public static double calculateHandlingQuality(int staffCount, int warehouseCapacity, double averageWage) {
        // Staff density: workers per 1000 m²
        double staffDensity = (staffCount / (warehouseCapacity / 1000.0));
        
        // Wage factor: higher wages correlate with better training/care
        double wageFactor = averageWage / 2500.0; // Normalize to avg wage of $2500
        
        // Combined quality: staff density + wage quality
        double handlingQuality = (staffDensity * 0.5) + (wageFactor * 0.5);
        
        return Math.min(1.0, Math.max(0.5, handlingQuality));
    }
    
    /**
     * Simulates return rate based on product quality and handling.
     * Poor handling + cheap manufacturer = higher returns
     * Good handling + premium manufacturer = lower returns
     * 
     * Returns: Return rate as decimal (0.05 = 5% return rate)
     */
    public static double simulateReturnRate(int productRating) {
        // Base return rate for this rating
        // Rating 100 = 2% returns, Rating 50 = 8% returns, Rating 0 = 15% returns
        double baseReturnRate = 0.15 - (productRating / 100.0 * 0.13);
        
        // Add small random variation (±2%)
        double variation = -0.02 + (random.nextDouble() * 0.04);
        
        return Math.max(0.01, Math.min(0.20, baseReturnRate + variation)); // Clamp 1-20%
    }
    
    /**
     * Example usage showing how to apply demand modifier to base demand
     */
    public static void printDemandModifierExample() {
        System.out.println("\n=== DEMAND MODIFIER EXAMPLE ===");
        
        // Example parameters
        String productType = "Handhelds";
        String season = "summer";
        int productRating = 75;  // Good product (0-100)
        double ourPrice = 89.99;
        double competitorPrice = 99.99;
        boolean isNew = true;
        boolean isOnDiscount = false;
        
        Product product = new Product();
        // Calculate modifier
        double modifier = calculateDemandModifier(product, season, productRating, competitorPrice, isOnDiscount);
        
        System.out.println("Product Type: " + productType);
        System.out.println("Season: " + season);
        System.out.println("Product Rating: " + productRating + "/100");
        System.out.println("Our Price: $" + ourPrice);
        System.out.println("Competitor Price: $" + competitorPrice);
        System.out.println("Is New: " + isNew);
        System.out.println("Is On Discount: " + isOnDiscount);
        System.out.println("\nFinal Demand Modifier: " + modifier + "x");
        System.out.println("If base demand = 100 units, actual demand = " + (int)(100 * modifier) + " units");
    }
}
