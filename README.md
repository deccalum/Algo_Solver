```mermaid
classDiagram
    class Customer {
        -id:int
        -name:String
        -email:String
    }

    class Product {
        -id:int
        -name:String
        -price:double
    }

    class Order {
        -id:int
        -totalPrice:double
    }

    Order "0..*" --> "1" Customer : belongsTo
    Order "1" --> "1..*" Product : contains

```