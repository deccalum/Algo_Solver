package se.lexicon;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.Random;
import java.util.Collections;
import java.time.*;
import java.time.format.DateTimeFormatter;

public class Main {
    private final static Random random = new Random();

    public static void main(String[] args) {

        List<Product> products = generateProducts(5);
        System.out.println(String.format("%-20s %-20s %-10s %-6s", "PRODUCT ID", "NAME", "PRICE", "STOCK"));
        products.forEach(System.out::println); // #
        System.out.println();

        int orderNumber = 1;
        LocalDateTime orderTime = LocalDateTime.now();
        final int ORDER_INTERVAL_MINUTES = 5;

        while (hasStock(products)) {

            Customer customer = Customer.generateCustomer();
            System.out.println("INCOMING ORDER FROM CUSTOMER");
            System.out.println(String.format("%-12s %-20s %-25s", "ID", "NAME", "EMAIL"));
            System.out.println(customer + "\n");

            Order order = purchaseOrder(customer, products, orderTime);
            System.out.println(order + "\n");
            System.out.println("UPDATED PRODUCT STOCK");
            products.forEach(System.out::println); // #
            System.out.println();

            try {
                TimeUnit.SECONDS.sleep(3);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            orderNumber++;
            orderTime = orderTime.plusMinutes(ORDER_INTERVAL_MINUTES);

        }
    }

    // Simple boolean to check if any products have stock left
    private static boolean hasStock(List<Product> products) {
        return products.stream().anyMatch(p -> p.getStock() > 0); // #
    }

    // Generate and return a list of products
    private static List<Product> generateProducts(int count) {
        List<Product> list = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            list.add(new Product().generateProduct());
        }
        return list;
    }

    // Simulate a customer purchasing products
    private static Order purchaseOrder(Customer customer, List<Product> availableProducts, LocalDateTime orderTime) {
        List<OrderItem> orderItems = new ArrayList<>();
        List<Product> shuffledProducts = new ArrayList<>(availableProducts);

        // instead of listing products with amount + return then picking random we use
        // shuffle
        Collections.shuffle(shuffledProducts);

        // Pick random number of products (that are in stock)
        List<Product> productsWithStock = new ArrayList<>();
        for (Product p : shuffledProducts) {
            if (p.getStock() > 0) {
                productsWithStock.add(p);
            }
        }

        // If no products in stock, return empty order
        if (productsWithStock.isEmpty()) {
            return new Order(customer, orderItems, orderTime);
        }

        // Customer picks 1-3 random products from those with stock
        int productCount = random.nextInt(1, Math.min(4, productsWithStock.size() + 1));

        // For each selected product, pick a random quantity (1-5) within available
        // stock
        for (int i = 0; i < productCount; i++) {
            Product product = productsWithStock.get(i);

            // picks random quantity from 1 to min of 5 OR available stock. If stock is eg 3
            // math.min will return 3
            int quantity = random.nextInt(1, Math.min(6, product.getStock() + 1));
            orderItems.add(new OrderItem(product, quantity));
            product.reduceStock(quantity);
        }

        return new Order(customer, orderItems, orderTime);
    }

    // CAN BE MOVED
    public static class Customer {
        private int customerID;
        private String name;
        private String email;

        public Customer() {
        }

        public Customer(int customerID, String name, String email) {
            this.customerID = customerID;
            this.name = name;
            this.email = email;
        }

        public static Customer generateCustomer() {
            Customer customer = new Customer();
            customer.customerID = Generators.randID();
            String[] nameAndEmail = Generators.generateCustomerNameAndEmail();
            customer.name = nameAndEmail[0];
            customer.email = nameAndEmail[1];
            return customer;
        }

        public int getCustomerID() {
            return customerID;
        }

        public String getName() {
            return name;
        }

        public String getEmail() {
            return email;
        }

        public void setCustomerID(int customerID) {
            this.customerID = customerID;
        }

        public void setName(String name) {
            this.name = name;
        }

        public void setEmail(String email) {
            this.email = email;
        }

        @Override
        public String toString() {
            return String.format("%-12d %-20s %-25s", customerID, name, email);
        }
    }

    public static class Product {
        private String productID;
        private String[] name;
        private double price;
        private int stock;
        private String category;

        public Product() {
        }

        public Product(String productID, String[] name, double price, int stock, String category) {
            this.productID = productID;
            this.name = name;
            this.price = price;
            this.stock = stock;
            this.category = category;
        }

        public Product generateProduct() {
            this.productID = Generators.productIDGenerator();
            this.name = Generators.productGenerator();
            this.price = Generators.priceGenerator(this.name[0], this.name[1]);
            this.stock = Generators.stockGenerator();
            // Always derive category from product type to ensure consistency
            this.category = Generators.categoryFor(this.name[1]);
            return this;
        }

        public void reduceStock(int quantity) {
            if (quantity > stock) {
                throw new IllegalArgumentException("Insufficient stock for product: " + productID);
            }
            this.stock -= quantity;
        }

        public void setStock(int stock) {
            this.stock = stock;
        }

        public void setPrice(double price) {
            this.price = price;
        }

        public void setCategory(String category) {
            this.category = category;
        }

        public String getProductID() {
            return productID;
        }

        public String[] getName() {
            return name;
        }

        public double getPrice() {
            return price;
        }

        public int getStock() {
            return stock;
        }

        public String getCategory() {
            return category;
        }

        @Override
        public String toString() {
            return String.format(java.util.Locale.US, "%-20s %-20s $%-9.2f %-6d",
                    productID, String.join(" ", name), price, stock);
        }
    }

    public static class OrderItem {
        private final Product product;
        private final int quantity;
        private final double subtotal;

        public OrderItem(Product product, int quantity) {
            this.product = product;
            this.quantity = quantity;
            this.subtotal = product.getPrice() * quantity;
        }

        public Product getProduct() {
            return product;
        }

        public int getQuantity() {
            return quantity;
        }

        public double getSubtotal() {
            return subtotal;
        }

        @Override
        public String toString() {
            return quantity + "x " + String.join(" ", product.getName()) +
                    " @ $" + product.getPrice() + " = $" + subtotal;
        }
    }

    public static class Order {
        private final String orderID;
        private final Customer customer;
        private final List<OrderItem> items;
        private final double total;
        private final LocalDateTime orderTimeStamp;

        public Order(Customer customer, List<OrderItem> items, LocalDateTime orderTimeStamp) {
            this.orderID = "ORD-" + UUID.randomUUID().toString().substring(0, 8);
            this.customer = customer;
            this.items = new ArrayList<>(items);
            this.total = calculateTotal(this.items);
            this.orderTimeStamp = orderTimeStamp;
        }

        private double calculateTotal(List<OrderItem> items) {
            return items.stream().mapToDouble(OrderItem::getSubtotal).sum();
        }

        public String getOrderID() {
            return orderID;
        }

        public Customer getCustomer() {
            return customer;
        }

        public List<OrderItem> getItems() {
            return new ArrayList<>(items);
        }

        public double getTotal() {
            return total;
        }

        public LocalDateTime getOrderTimeStamp() {
            return orderTimeStamp;
        }

        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd/MM HH:mm");
            sb.append(String.format("%-12s  %-20s\n", orderID, orderTimeStamp.format(formatter)));
            sb.append(String.format("%-4s %-20s %-10s %-10s\n", "QT", "Product", "UnitPrice", "Subtotal"));
            for (OrderItem item : items) {
                sb.append(String.format(java.util.Locale.US, "%-4d %-20s $%-9.2f $%-9.2f\n",
                        item.getQuantity(),
                        String.join(" ", item.getProduct().getName()),
                        item.getProduct().getPrice(),
                        item.getProduct().getCategory(),
                        item.getSubtotal()));
            }
            return sb.toString();
        }
    }
}

/*
 * StringBuilder in Java is a mutable sequence of characters used to efficiently
 * build and modify strings. Unlike regular String objects, which are immutable
 * (every modification creates a new object), StringBuilder allows you to
 * append, insert, delete, or modify characters without creating new objects
 * each time.
 * 
 * How it works:
 * Internally, it uses a resizable character array.
 * Methods like.append(),.insert(),.delete(),and.replace() modify the contents
 * directly.
 * It's much faster than using string concatenation (+) in loops or repeated
 * operations.
 * When you're done building the string, you can call .toString() to get the
 * final String.
 */

/*
 * forEach method in Java:
 *
 * The forEach method is used to iterate over each element in a collection (like
 * a List).
 * It takes a lambda expression or method reference as an argument and applies
 * it to every element.
 *
 * Example:
 * products.forEach(System.out::println);
 * This will call System.out.println(product) for each product in the products
 * list.
 *
 * It's a concise and readable way to perform an action on every item in a
 * collection.
 */

/*
 * Lambda expressions in Java:
 *
 * A lambda expression is a concise way to represent an anonymous function (a
 * block of code that can be passed around).
 * It is often used to implement methods of functional interfaces (interfaces
 * with a single abstract method).
 *
 * Syntax example:
 * (parameters) -> expression or { statements }
 *
 * Example with streams:
 * products.stream().anyMatch(p -> p.getStock() > 0);
 * Here, p -> p.getStock() > 0 is a lambda expression that checks if a product
 * has stock.
 *
 * Lambdas make code shorter and more readable, especially when working with
 * collections and functional-style operations.
 */

/*
 * Streams in Java:
 *
 * A Stream is a sequence of elements supporting functional-style operations on
 * collections.
 * Streams allow you to process data declaratively (what to do, not how to do
 * it).
 *
 * Common stream operations include:
 * - filter: select elements based on a condition
 * - map: transform elements
 * - forEach: perform an action for each element
 * - anyMatch, allMatch: check if any/all elements match a condition
 * - collect: gather results into a collection or value
 *
 * Example:
 * products.stream().anyMatch(p -> p.getStock() > 0);
 * This creates a stream from the products list and checks if any product has
 * stock.
 *
 * Streams make code more concise and readable, especially for complex data
 * processing.
 */