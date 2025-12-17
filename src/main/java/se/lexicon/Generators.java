package se.lexicon;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import java.util.Random;

public class Generators {

    public static String[] randFirstNames = { "Simon", "Anna", "Peter", "Maria", "John", "Anna", "Peter", "Maria",
            "John",
            "Linda", "James", "Susan", "Robert", "Karen" };

    public static String[] randLastNames = { "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
            "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson" };

    public static String[] randEmailProviders = { "fmail.com", "ahooy.com", "inlook.com", "example.com",
            "notmail.com" };

    public static String[] randProductVersions = { "Pro", "Max", "Ultra", "Mini", "Plus", "Air", "Go", "Lite",
            "Prime", "Edge" };

    public static String[] randProductTypes = { "Phone", "Laptop", "Tablet", "Headphones", "Camera", "Smartwatch",
            "Speaker", "Monitor",
            "Printer", "Router" };

    public static int randID() {
        int randID = UUID.randomUUID().hashCode();
        if (randID < 0) {
            randID = -randID;
        }
        return randID;
    }

    public static String productIDGenerator() {
        return "PROD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    public static double priceGenerator() {
        Random rand = new Random();
        return Math.round(10 + (5000 - 10) * rand.nextDouble());
    }

    public static int stockGenerator() {
        Random rand = new Random();
        return rand.nextInt(1, 21);
    }

    public static String[] productNameGenerator() {
        Random rand = new Random();
        String ver = randProductVersions[rand.nextInt(randProductVersions.length)];
        String typ = randProductTypes[rand.nextInt(randProductTypes.length)];
        return new String[] { ver, typ };
    }

    public static String[] generateCustomerNameAndEmail() {
        Random rand = new Random();
        String firstName = randFirstNames[rand.nextInt(randFirstNames.length)];
        String lastName = randLastNames[rand.nextInt(randLastNames.length)];
        String provider = randEmailProviders[rand.nextInt(randEmailProviders.length)];

        String fullName = firstName + " " + lastName;
        String email = (firstName.substring(0, 1) + lastName).toLowerCase() + "@" + provider;

        return new String[] { fullName, email };
    }

}