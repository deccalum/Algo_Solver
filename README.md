# Algo Solver

**Full-stack optimization platform**: Python optimization engine + React UI

## TODO

### FOR VITE GUI

* add database view
* add SQL queries and other commands.
* add option to export data to CSV or Excel.
* add filters and sorting options for the data.

* clearly seperate layers GENERATION -> SOLVER
* add compare between outputs of different configurations
* program needs to runable without setting certain fields like eg. demand.

#### IMPLEMENTATION

1. The Python FastAPI backend provides all API endpoints. Frontend connects directly to Python on port 18000.

2. Database view is implemented with Ag-Grid in React.

3. Database operations are handled by Python SQLAlchemy. Data export and queries work through the API.

Find a way to simplify testing different functions and features. GUI should expose different versions of the algorithm with different parameters. add a way to compare results and performance of different versions.

#### MISC

##### resolve `python/generator.py` 

```python
ProductItemMessage = getattr(algsolver_pb2, "ProductItem")
```

* rewrite the code to use the generated protobuf classes directly.

* use a more dynamic approach to access the protobuf classes, such as using a factory pattern or a registry of classes.

* write the protobuf classes in a way that they can be easily accessed without needing to use `getattr`.

