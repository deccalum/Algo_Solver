
public class Product {
    private String[] product;
    private String productID;
    private String category;
    private double price; // wholesale/cost price - what the store pays
    private double retailPrice; // retail price - what customers pay
    private int size;
    private int weight;
    private int stock;
    // private int handling; // to increase warehouse staff needs and or time to pick
    // private int fragility; // to increase ship cost
    // private int minOrderQuantity;
    // private int leadTime;
    // private int bulkDiscount;
    // private int demand;
    private boolean isNew;

    public Product() {
    }

    public Product(String productID, String[] product, String category, double price, int size, int weight, int stock, boolean isNew) {
        this.productID = productID;
        this.product = product;
        this.category = category;
        this.price = price;
        this.retailPrice = calculateInitialRetailPrice(price); // Calculate retail price on creation
        this.size = size;
        this.weight = weight;
        this.stock = stock;
        this.isNew = isNew;
    }

    public Product generateProduct() {
        this.productID = Generators.productID();
        this.product = Generators.productGenerator();

        String version = this.product[0];
        String type = this.product[1];

        this.category = Generators.productCategory(type);
        this.price = Generators.productPrice(version, type); // wholesale cost
        
        // Initialize with base markup before demand modifiers applied
        this.retailPrice = calculateInitialRetailPrice(this.price);

        int[] metrics = Generators.productMetrics(version, type);
        this.size = metrics[0];
        this.weight = metrics[1];
        
        this.stock = Generators.productStock();
        this.isNew = true; // New products are marked as new
        return this;
    }
    
    private double calculateInitialRetailPrice(double wholesalePrice) {
        // Base markup of 50% before demand modifiers
        return wholesalePrice * 1.5;
    }

    public void setPrice(double price) {
        this.price = price;
    }
    
    public void setRetailPrice(double retailPrice) {
        this.retailPrice = retailPrice;
    }
    
    public void setCategory(String category) {
        this.category = category;
    }
    public void setSize(int size) {
        this.size = size;
    }
    public void setWeight(int weight) {
        this.weight = weight;
    }
    public void setStock(int stock) {
        this.stock = stock;
    }
    public void reduceStock(int quantity) {
        if (quantity > stock) {
            throw new IllegalArgumentException("Insufficient stock for product: " + productID);
        }
        this.stock -= quantity;
    }
    
    public void setIsNew(boolean isNew) {
        this.isNew = isNew;
    }
    
    /**
     * Updates retail price based on demand modifiers
     * @param season Current season
     * @param productRating Product quality rating (0-100)
     * @param competitorPrice Competitor's price (0 if unknown)
     * @param discounted Whether product is on sale
     */
    public void updateRetailPriceWithDemand(String season, int productRating, double competitorPrice, boolean discounted) {
        double demandMultiplier = DemandModifier.calculateDemandModifier(
            this, season, productRating, competitorPrice, discounted
        );
        
        // Apply demand multiplier to base retail price
        double baseRetailPrice = this.price * 1.5; // 50% base markup
        this.retailPrice = baseRetailPrice * demandMultiplier;
    }

    public double stockCost(double price, int quantity, int size) {
        return (price * quantity ) * size; // product ship cost in seperate method
    }
    public double profitMargin(double price, double retailPrice, int stockCost, int quantity, int demand) {
        return (price - retailPrice - stockCost ) * demand;
    }
    public double velocity(int demand, int stock, int timePeriod) {
        return (demand / stock ) * timePeriod;
    }

    public String getProductID() {
        return productID;
    }
    public String[] getName() {
        return product;
    }
    public String getCategory() {
        return category;
    }
    public double getPrice() {
        return price; // wholesale/cost price
    }
    public double getRetailPrice() {
        return retailPrice; // customer-facing price
    }
    public int getSize() {
        return size;
    }
    public int getWeight() {
        return weight;
    }
    public int getStock() {
        return stock;
    }
    public boolean isNew() {
        return isNew;
    }

    @Override
    public String toString() {
        return String.format(java.util.Locale.US, "%-15s %-20s %-15s Cost:$%-9.2f Retail:$%-9.2f %-10s %-10s %-6d",
                productID, product[0] + " " + product[1], category, price, retailPrice, size + "cm", weight + "g", stock);
    }
}
/*
public class Relations {

    New class ProductRelationships:

    getRelated(Product) → returns list of complementary products
    Desktop → Monitor, Keyboard, Mouse
    Laptop → Laptop Bag, USB Hub, Cooling Pad
    Earbuds → Phone cases, charging cables

        
    getRelationshipStrength(Product, Product) → how strongly related (0.0-1.0)
    suggestBundle(Product, StoreSize) → recommend related products based on warehouse
}
*/