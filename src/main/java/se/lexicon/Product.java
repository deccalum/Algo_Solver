package se.lexicon;

public class Product {
    private String[] product;
    private String productID;
    private String category;
    private double price;
    private double retailPrice;
    private int size;
    private int weight;
    private int stock;
    private int handling; // to increase warehouse staff needs and or time to pick
    private int fragility; // to increase ship cost
    private int minOrderQuantity;
    private int leadTime;
    private int bulkDiscount;
    private int demand;
    private boolean isNew;

    public Product() {
    }

    public Product(String productID, String[] product, String category, double price, int size, int weight, int stock, boolean isNew) {
        this.productID = productID;
        this.product = product;
        this.category = category;
        this.price = price;
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
        this.price = Generators.productPrice(version, type);

        int[] metrics = Generators.productMetrics(version, type);
        this.size = metrics[0];
        this.weight = metrics[1];
        
        this.stock = Generators.productStock();
        return this;
    }

    public void setPrice(double price) {
        this.price = price;
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

    public double retailPrice(double price) {
        // retail price calculated base on ... can lower if demand is low or in need to clear stock - if product is returned with opened box 
        /*
        intelligent retail price. base on demand, stock levels, trends. 
        should be modifable for sales and discounts
        */
       return price * 1.2; // simple 20% markup for now
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
    public double getRetailPrice() {
        return retailPrice;
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

    @Override
    public String toString() {
        return String.format(java.util.Locale.US, "%-15s %-20s %-15s $%-9.2f %-10s %-10s %-6d",
                productID, product[0] + " " + product[1], category, price, size + "cm", weight + "g", stock);
    }

    public boolean isNew() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'isNew'");
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