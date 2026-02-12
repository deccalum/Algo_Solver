
public class Customer {
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