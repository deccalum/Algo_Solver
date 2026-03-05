# Algo Solver

**Full-stack optimization platform**: Python optimization engine + Spring Boot API + React UI

## TODO

### FOR VITE GUI

* add database view
* add SQL queires and other commands.
* add option to export data to CSV or Excel.
* add filters and sorting options for the data.

* clearly seperate layers GENERATION -> SOLVER
* add compare between outputs of different configurations
* program needs to runable without setting certain fields like eg. demand.

#### IMPLEMENTATION

1. populate java packages: ``dto``, ``dao``,``repository``, ``service``, ``controller``. add java classes for each package. implement basic functionality for each class. wire up the GUI to the backend services.`

2. Find and insert typescript/javascript+css database template.

3. add database connection and queries. implement data insertion and update operations. add postgres python functions for data manipulation and retrieval. organize arg runs and other backend processes. wire to GUI.

Find a way to simplify testing different functions and features. GUI should expose different versions of the algorithm with different parameters. add a way to compare results and performance of different versions.

#### MISC

##### resolve `python/generator.py` 

```python
ProductItemMessage = getattr(algsolver_pb2, "ProductItem")
```

* rewrite the code to use the generated protobuf classes directly.

* use a more dynamic approach to access the protobuf classes, such as using a factory pattern or a registry of classes.

* write the protobuf classes in a way that they can be easily accessed without needing to use `getattr`.

