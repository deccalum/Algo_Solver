
import java.time.LocalDateTime;
import java.util.Random;
import java.util.UUID;

public class Generators {

    private final static Random random = new Random();

    public static String[] firstNames = { "Simon", "Anna", "Peter", "Maria", "John", "Anna", "Peter", "Maria",
            "John",
            "Linda", "James", "Susan", "Robert", "Karen" };

    public static String[] lastNames = { "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
            "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson" };

    public static String[] randEmailProviders = { "@fmail.com", "@ahooy.com", "@inlook.com", "@example.com",
            "@notmail.com" };

    private static final Object[][] productVersion = {
            { "Lite", 0.6 },
            { "Mini", 0.7 },
            { "Go", 0.8 },
            { "Air", 0.85 },
            { "Plus", 1.0 },
            { "Prime", 1.2 },
            { "Pro", 1.3 },
            { "Max", 1.5 },
            { "Ultra", 1.8 },
            { "Edge", 1.9 }
    };

    private static final Object[][] productType = {
            { "Phone", 1.0, "Handhelds" },
            { "Laptop", 7.5, "Computers" },
            { "Desktop", 10.0, "Computers" },
            { "Tablet", 5.0, "Handhelds" },
            { "Headphones", 0.8, "Audio" },
            { "Earbuds", 0.5, "Audio" },
            { "Camera", 1.4, "Imaging" },
            { "Smart TV", 3.0, "Entertainment" },
            { "Smartwatch", 0.9, "Wearables" },
            { "Speaker", 0.7, "Audio" },
            { "Monitor", 5.0, "Computers" },
            { "Printer", 1.1, "Computers" },
            { "Router", 0.6, "Networking" }
    };

    // quick store names. expand based on product range later
    private static final Object[][] storeNames = {
            { "Tech Haven" },
            { "Gadget Galaxy" },
            { "Device Depot" },
            { "Electro Emporium" },
            { "Digital Den" },
            { "Gizmo Garage" },
            { "Widget World" },
            { "Techno Tower" },
            { "Circuit City" },
            { "Pixel Palace" }
    };


    // ID/NAME GENERATORS
    public static int randID() {
        int randID = UUID.randomUUID().hashCode();
        if (randID < 0) {
            randID = -randID;
        }
        return randID;
    }

    public static String[] generateCustomerNameAndEmail() {
        String firstName = firstNames[random.nextInt(firstNames.length)];
        String lastName = lastNames[random.nextInt(lastNames.length)];
        String provider = randEmailProviders[random.nextInt(randEmailProviders.length)];

        String fullName = firstName + " " + lastName;
        String email = (firstName.substring(0, 1) + lastName).toLowerCase() + provider;

        return new String[] { fullName, email };
    }

    // PRODUCT GENERATORS
    public static String productID() {
        return "PROD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    public static String[] productGenerator() {
        Object[] verRow = productVersion[random.nextInt(productVersion.length)];
        Object[] prodRow = productType[random.nextInt(productType.length)];

        String version = verRow[0].toString();
        String type = prodRow[0].toString();
        String category = prodRow[2].toString();

        // Return version, type, and category to match caller expectations
        return new String[] { version, type, category };
    }

    public static String productCategory(String category) {
        for (Object[] p : productType) {
            if (p[0].toString().equals(category)) {
                return p[2].toString();
            }
        }
        return "Unknown";
    }

    public static double productPrice(String version, String type) {
        // Base price range: $50-$80
        double basePrice = 50 + (80 - 50) * random.nextDouble();

        // Resolve modifiers by provided names (fallback to 1.0 if not found)
        double vMod = 1.0;
        for (Object[] v : productVersion) {
            if (v[0].toString().equals(version)) {
                vMod = (double) v[1];
                break;
            }
        }
        double tMod = 1.0;
        for (Object[] p : productType) {
            if (p[0].toString().equals(type)) {
                tMod = (double) p[1];
                break;
            }
        }
        // Small random variation
        double rMod = 0.90 + (random.nextDouble() * 0.10);
        double finalPrice = basePrice * vMod * tMod * rMod;
        // Round to 2 decimal places
        return Math.round(finalPrice * 100.0) / 100.0;
    }

    public static double productHandling(double weight, double fragility, double size) {
        return 2 * weight / 1000.0 + fragility * 0.5 + size / 10000.0;
    }
    /*
    public static int[] ratingGenerator() {
        int ratingsCount = random.nextInt(1, 501); // 1 to 500 ratings
        int averageRating = random.nextInt(1, 6); // 1 to 5 stars
        return new int[] { averageRating, ratingsCount };
    }
    */

    public static double productProfit(double price, double retailPrice, double handling) {
        return (retailPrice - price - handling);
    }

    public static double productProfitPerMeters(double productProfit, double size) {
        return productProfit / (size / 10000.0);
    }

    public static int[] productMetrics(String version, String type) {
        double vMod = 1.0, tMod = 1.0;
        for (Object[] v : productVersion) if (v[0].equals(version)) vMod = (double) v[1];
        for (Object[] t : productType) if (t[0].equals(type)) tMod = (double) t[1];

        int sizeSquared = (int) Math.pow(10 * tMod, 2);
        int weight = (int) (500 * vMod * tMod * random.nextDouble());
        return new int[] { sizeSquared, weight };
    }

    public static int productStock() {
        return random.nextInt(1, 21);
    }

    public static LocalDateTime randomOrderTimeGenerator(int orderIndex) {
        return LocalDateTime.now().plusMinutes(orderIndex * 5);
    }


    // STORE LOGICS
    public enum Warehouse { SMALL, MEDIUM, LARGE }
    public enum Store { SMALL, MEDIUM, LARGE }

    public static Store randomStoreSize() {
        return Store.values()[random.nextInt(Store.values().length)];
    }

    public static Warehouse randomWarehouseSize() {
        return Warehouse.values()[random.nextInt(Warehouse.values().length)];
    }

    public static Warehouse deriveWarehouseSize(Store s) {
        return switch (s) {
            case SMALL -> Warehouse.SMALL;
            case MEDIUM -> Warehouse.MEDIUM;
            case LARGE -> Warehouse.LARGE;
        };
    }

    public static String storeName() {
        Object[] pick = storeNames[random.nextInt(storeNames.length)];
        return (String) pick[0];
    }

    public static double storeBudget(Store size) {
        return switch (size) {
            case SMALL -> 10_000 + (30_000 - 10_000) * random.nextDouble();
            case MEDIUM -> 30_000 + (80_000 - 30_000) * random.nextDouble();
            case LARGE -> 80_000 + (200_000 - 80_000) * random.nextDouble();
        };
    }

    public static final int storeWage() {
        return 2000 + random.nextInt(5000 - 2000 + 1); // $2,000 to $5,000 per staff
    }

    public static final int warehouseWage() {
        return 1800 + random.nextInt(3000 - 1800 + 1); // $1,800 to $3,000 per staff
    }

    public static int storeEmployees(Store size) {
        return switch (size) {
            case SMALL -> random.nextInt(1, 2);
            case MEDIUM -> random.nextInt(2, 4);
            case LARGE -> random.nextInt(4, 10);
        };
    }

    public static int warehouseEmployees(Warehouse size) {
        return switch (size) {
            case SMALL -> random.nextInt(1, 2);
            case MEDIUM -> random.nextInt(3, 5);
            case LARGE -> random.nextInt(6, 11);
        };
    }

    public static double rent(Warehouse size) {
        // Rent per m²: larger warehouses cheaper per m²
        double perM2 = switch (size) {
            case SMALL -> 15 + (25 - 15) * random.nextDouble();
            case MEDIUM -> 10 + (18 - 10) * random.nextDouble();
            case LARGE -> 7 + (12 - 7) * random.nextDouble();
        };
        return perM2;
    }

    public static double utilities(Warehouse size) {
        return switch (size) {
            case SMALL -> 500 + (2000 - 500) * random.nextDouble();        // $500-$2,000
            case MEDIUM -> 2000 + (10000 - 2000) * random.nextDouble();    // $2,000-$10,000
            case LARGE -> 10000 + (50000 - 10000) * random.nextDouble();   // $10,000-$50,000
        };
    }

    public static int warehouseCapacity(Warehouse size) {
        return switch (size) {
            case SMALL -> random.nextInt(50, 1001);        // 50-1,000 m^2
            case MEDIUM -> random.nextInt(1001, 10001);  // 1,001-10,000 m^2
            case LARGE -> random.nextInt(10001, 100001); // 10,001-100,000 m^2
        };
    }
    

    //public static void importList(int size, double budget, int handling) {
        /*
        need demand (units sold) dont need more than demand.
        product relation, 
        wages


        15. Sort products by profitPerSquareMeter (descending)
        ↓
        16. Greedy selection loop:
            while (remainingBudget > 0 && remainingSpace > 0):
            → Pick next highest-profit product
            → Calculate max quantity that fits:
                maxByBudget = remainingBudget / manufacturerCost
                maxBySpace = remainingSpace / productSize
                maxByDemand = estimatedMonthlyDemand * safetyFactor
                
                quantity = min(maxByBudget, maxBySpace, maxByDemand)
            
            → Add to importList
            → Deduct from remainingBudget and remainingSpace
            → Recalculate staffing if needed (step 11-14)
        ↓
        17. Return Map<Product, Integer> (product → quantity)

         */
    

}