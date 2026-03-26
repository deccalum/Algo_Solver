from fastapi import FastAPI, Query, HTTPException
from sqlalchemy import create_engine, text
import os
import re
import json
import proto.algsolver_pb2 as algsolver_pb2

app = FastAPI()

def protobuf_to_dict(pb_obj):
    """Convert protobuf message to dictionary"""
    result = {}
    for field in pb_obj.DESCRIPTOR.fields:
        value = getattr(pb_obj, field.name)
        if field.type == field.TYPE_MESSAGE:
            if field.label == field.LABEL_REPEATED:
                result[field.name] = [protobuf_to_dict(item) for item in value]
            else:
                result[field.name] = protobuf_to_dict(value)
        else:
            result[field.name] = value
    return result

# Database connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/algosolver"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def _validate_table_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", name):
        raise HTTPException(status_code=400, detail="Invalid table name")
    return name


def _validate_column_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", name):
        raise HTTPException(status_code=400, detail="Invalid column name")
    return name


def _build_filter_where_clause(filter_model: dict) -> tuple[str, dict]:
    where_clauses = []
    params: dict[str, object] = {}

    for idx, (raw_column, details) in enumerate(filter_model.items()):
        if not isinstance(details, dict):
            continue

        column = _validate_column_name(raw_column)
        filter_type = details.get("filterType")
        operator = details.get("type", "equals")
        param_name = f"filter_{idx}"

        if filter_type == "text":
            value = details.get("filter", "")
            if operator == "contains":
                where_clauses.append(f'"{column}" ILIKE :{param_name}')
                params[param_name] = f"%{value}%"
            elif operator == "notContains":
                where_clauses.append(f'"{column}" NOT ILIKE :{param_name}')
                params[param_name] = f"%{value}%"
            elif operator == "startsWith":
                where_clauses.append(f'"{column}" ILIKE :{param_name}')
                params[param_name] = f"{value}%"
            elif operator == "endsWith":
                where_clauses.append(f'"{column}" ILIKE :{param_name}')
                params[param_name] = f"%{value}"
            else:
                where_clauses.append(f'"{column}" ILIKE :{param_name}')
                params[param_name] = str(value)

        elif filter_type == "number":
            value = details.get("filter")
            if value is None:
                continue

            op_map = {
                "equals": "=",
                "notEqual": "!=",
                "greaterThan": ">",
                "greaterThanOrEqual": ">=",
                "lessThan": "<",
                "lessThanOrEqual": "<=",
            }

            if operator == "inRange":
                param_name_to = f"filter_{idx}_to"
                value_to = details.get("filterTo")
                if value_to is None:
                    continue
                where_clauses.append(
                    f'"{column}" >= :{param_name} AND "{column}" <= :{param_name_to}'
                )
                params[param_name] = value
                params[param_name_to] = value_to
            else:
                sql_op = op_map.get(operator, "=")
                where_clauses.append(f'"{column}" {sql_op} :{param_name}')
                params[param_name] = value

    if not where_clauses:
        return "", params

    return f"WHERE {' AND '.join(where_clauses)}", params


@app.get("/api/database/tables")
def get_tables():
    try:
        with engine.connect() as conn:
            tables_result = conn.execute(
                text(
                    """
                    SELECT table_name AS name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    """
                )
            )
            tables = [dict(row) for row in tables_result.mappings().all()]

            for table in tables:
                try:
                    table_name = _validate_table_name(table["name"])
                    count_query = text(f'SELECT COUNT(*) AS row_count FROM "{table_name}"')
                    count = conn.execute(count_query).scalar()
                    table["row_count"] = int(count or 0)
                except Exception:
                    table["row_count"] = 0

            return tables
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not connected: {e}")

@app.get("/api/database/tables/{name}/data")
def get_table_data(
    name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    filters: str | None = Query(default=None),
):
    table_name = _validate_table_name(name)

    filter_model: dict = {}
    if filters:
        try:
            parsed = json.loads(filters)
            if isinstance(parsed, dict):
                filter_model = parsed
            else:
                raise HTTPException(status_code=400, detail="Invalid filter model")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid filters JSON")

    where_clause, filter_params = _build_filter_where_clause(filter_model)
    query = text(
        f'SELECT * FROM "{table_name}" {where_clause} LIMIT :limit OFFSET :offset'
    )
    params = {"limit": limit, "offset": offset, **filter_params}

    try:
        with engine.connect() as conn:
            result = conn.execute(query, params)
            return [dict(row) for row in result.mappings().all()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/database/tables/{name}/schema")
def get_table_schema(name: str):
    table_name = _validate_table_name(name)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT column_name AS name, data_type AS type
                    FROM information_schema.columns
                    WHERE table_name = :table_name AND table_schema = 'public'
                    ORDER BY ordinal_position
                    """
                ),
                {"table_name": table_name},
            )
            return [dict(row) for row in result.mappings().all()]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not connected: {e}")

@app.get("/api/db/status")
def get_db_status():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not connected: {e}")

@app.get("/api/config")
def get_config():
    from config.dev_default import build_dev_config
    config = build_dev_config()
    # Convert protobuf to dict for JSON response
    return protobuf_to_dict(config)

@app.post("/api/generate-catalog")
def generate_catalog(request: dict):
    from config.dev_default import build_dev_config
    from core.generator import ProductGenerator
    
    # Use provided config or default
    if 'config' in request:
        # TODO: Convert dict back to protobuf config
        config = build_dev_config()
    else:
        config = build_dev_config()
    
    generator = ProductGenerator.from_proto_config(config)
    products = generator.generate()
    
    return {
        "products": [protobuf_to_dict(p) for p in products],
        "generated_count": len(products)
    }

@app.post("/api/optimize-catalog")
def optimize_catalog(request: dict):
    from config.dev_default import build_dev_config
    from core.solver import ProcurementOptimizer, SolverConfig
    
    config = build_dev_config()
    products = request.get('products', [])
    
    optimizer = ProcurementOptimizer(
        SolverConfig(
            budget_constraint=config.generation.budget,
            space_constraint=config.generation.space,
        )
    )
    result = optimizer.optimize(products)
    
    return {
        "status": result.get("status", "UNKNOWN"),
        "objective_value": float(result.get("objective_value", 0.0)),
        "selected_count": len(result.get("product_totals", {}))
    }

@app.post("/api/estimate-products")
def estimate_products(request: dict):
    price_min = request.get('price_min', 1.0)
    price_max = request.get('price_max', 10000.0)
    size_min = request.get('size_min', 0.1)
    size_max = request.get('size_max', 100000.0)
    price_zones = request.get('price_zones', [])
    size_zones = request.get('size_zones', [])
    
    # Simple estimation logic
    price_span = max(0.0, price_max - price_min)
    size_span = max(0.0, size_max - size_min)
    
    def zone_points(span: float, zone) -> int:
        if zone.get('mode', '').strip().lower() == "exact":
            step = max(1e-9, zone.get('step', 1.0))
            return max(1, int(span / step) + 1)
        return max(1, int(zone.get('resolution', 10)))
    
    price_points = 0
    for zone in price_zones:
        price_points += zone_points(price_span * max(0.0, zone.get('span_share', 1.0)), zone)
    
    size_points = 0
    for zone in size_zones:
        size_points += zone_points(size_span * max(0.0, zone.get('span_share', 1.0)), zone)
    
    estimated = max(1, price_points) * max(1, size_points)
    
    return {
        "estimated_products": estimated,
        "strategy": "zone_based"
    }