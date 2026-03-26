def init_schema(conn):
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS products (
            id           VARCHAR(10) PRIMARY KEY,
            price        INTEGER,
            size         INTEGER,
            logistics    FLOAT,
            transit      VARCHAR(20),
            transit_size FLOAT,
            transit_cost FLOAT,
            demand       FLOAT,
            markup       FLOAT,
            stock        INTEGER
        )
    """)
    conn.commit()