package se.lexicon;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.Random;
import java.util.Collections;

public class Main {

    public static void main(String[] args) {
        // Generate products
        List<Product> products = generateProducts(5);
        System.out.println("Available products:");
        products.forEach(System.out::println);
        System.out.println();

        int orderNumber = 1;
        while (hasStock(products)) {

            // Generate customer and create order
            Customer customer = new Customer().generateCustomer();
            System.out.println("Customer:");
            System.out.println(customer);
            System.out.println();

            Order order = purchaseOrder(customer, products);
            System.out.println("Order" + orderNumber + " created:");
            System.out.println(order);
            System.out.println();

            System.out.println("Updated stock after order:");
            products.forEach(System.out::println);

            try {
                TimeUnit.SECONDS.sleep(2);
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            orderNumber++;
        }
        // inti loop
        // order with products
        // ordercreated= -stock
        // update stock

        // lateer continue until stock is out of all products
    }

    private static boolean hasStock(List<Product> products) {
        return products.stream().anyMatch(p -> p.getStock() > 0);
    }

    private static List<Product> generateProducts(int count) {
        List<Product> list = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            list.add(new Product().generateProduct());
        }
        return list;
    }

    private static Order purchaseOrder(Customer customer, List<Product> availableProducts) {
        List<OrderItem> orderItems = new ArrayList<>();
        Random rand = new Random();
        List<Product> shuffled = new ArrayList<>(availableProducts);
        Collections.shuffle(shuffled);

        // Pick random number of products (that are in stock)
        List<Product> productsWithStock = new ArrayList<>();
        for (Product p : shuffled) {
            if (p.getStock() > 0) {
                productsWithStock.add(p);
            }
        }

        // If no products in stock, return empty order
        if (productsWithStock.isEmpty()) {
            return new Order(customer, orderItems);
        }

        // Customer picks 1-3 random products from those with stock
        int productCount = rand.nextInt(1, Math.min(4, productsWithStock.size() + 1));

        for (int i = 0; i < productCount; i++) {
            Product product = productsWithStock.get(i);
            int quantity = rand.nextInt(1, Math.min(6, product.getStock() + 1));
            orderItems.add(new OrderItem(product, quantity));
            product.reduceStock(quantity);
        }

        return new Order(customer, orderItems);
    }

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

        public Customer generateCustomer() {
            this.customerID = Generators.randID();
            String[] nameAndEmail = Generators.generateCustomerNameAndEmail();
            this.name = nameAndEmail[0];
            this.email = nameAndEmail[1];
            return this;
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
            return "Customer{id=" + customerID + ", name='" + name + "', email='" + email + "'}";
        }
    }

    public static class Product {
        private String productID;
        private String[] name;
        private double price;
        private int stock;

        public Product() {
        }

        public Product(String productID, String[] name, double price, int stock) {
            this.productID = productID;
            this.name = name;
            this.price = price;
            this.stock = stock;
        }

        public Product generateProduct() {
            this.productID = Generators.productIDGenerator();
            this.name = Generators.productNameGenerator();
            this.price = Generators.priceGenerator();
            this.stock = Generators.stockGenerator();
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

        @Override
        public String toString() {
            return "Product{id=" + productID + ", name='" + String.join(" ", name) + "', price=" + price + ", stock="
                    + stock + "}";
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

        public Order(Customer customer, List<OrderItem> items) {
            this.orderID = "ORD-" + UUID.randomUUID().toString().substring(0, 8);
            this.customer = customer;
            this.items = new ArrayList<>(items);
            this.total = calculateTotal(this.items);
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

        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            sb.append("Order{id=").append(orderID)
                    .append(", customer=").append(customer.getName())
                    .append(", total=$").append(total)
                    .append("}\nItems:\n");
            items.forEach(item -> sb.append("  - ").append(item).append("\n"));
            return sb.toString();
        }
    }
}