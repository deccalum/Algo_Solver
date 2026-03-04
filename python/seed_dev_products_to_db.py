import os
from typing import Any, Iterable

from dev_default import dev_default
from generator import ProductGenerator


def _require_psycopg():
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'psycopg'. Install with: pip install psycopg[binary]"
        ) from exc
    return psycopg


def _rows(products: Iterable[Any]):
    for product in products:
        yield (
            product.id,
            int(product.price),
            int(product.size),
            float(product.logistics),
            str(product.transit),
            float(product.transit_size),
            float(product.transit_cost),
            float(product.demand),
            float(product.markup),
            int(product.stock),
        )


def main() -> None:
    psycopg = _require_psycopg()

    use_transit_v2 = os.getenv("USE_TRANSIT_V2", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    generator = ProductGenerator.from_proto_config(
        dev_default, use_transit_v2=use_transit_v2
    )
    products = generator.generate()

    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="algosolver",
        user="postgres",
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dev_products (
                    id text PRIMARY KEY,
                    price integer NOT NULL,
                    size integer NOT NULL,
                    logistics double precision NOT NULL,
                    transit text NOT NULL,
                    transit_size double precision NOT NULL,
                    transit_cost double precision NOT NULL,
                    demand double precision NOT NULL,
                    markup double precision NOT NULL,
                    stock integer NOT NULL
                )
                """
            )
            cur.execute("TRUNCATE TABLE dev_products")
            cur.executemany(
                """
                INSERT INTO dev_products (
                    id, price, size, logistics, transit,
                    transit_size, transit_cost, demand, markup, stock
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                list(_rows(products)),
            )
            cur.execute("SELECT COUNT(*) FROM dev_products")
            count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT id, price, size, transit, transit_cost
                FROM dev_products
                ORDER BY id
                LIMIT 5
                """
            )
            sample = cur.fetchall()

    print(f"mode={'V2_MIN_TOTAL_COST' if use_transit_v2 else 'V1_RULE_WEIGHTED'}")
    print(f"generated={len(products)}")
    print(f"inserted={count}")
    print("sample_rows=")
    for row in sample:
        print(row)


if __name__ == "__main__":
    main()
