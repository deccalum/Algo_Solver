DO $$
BEGIN
    BEGIN
        CREATE EXTENSION IF NOT EXISTS plpython3u;
        RAISE NOTICE 'plpython3u extension is available.';
    EXCEPTION
        WHEN insufficient_privilege THEN
            RAISE NOTICE 'Skipping plpython3u extension (insufficient privilege).';
        WHEN undefined_file THEN
            RAISE NOTICE 'Skipping plpython3u extension (extension not installed).';
        WHEN others THEN
            RAISE NOTICE 'Skipping plpython3u extension: %', SQLERRM;
    END;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'plpython3u') THEN
        EXECUTE $fn$
            CREATE OR REPLACE FUNCTION estimate_product_count_plpy(
                price_min DOUBLE PRECISION,
                price_max DOUBLE PRECISION,
                size_min DOUBLE PRECISION,
                size_max DOUBLE PRECISION,
                price_resolution INTEGER,
                size_resolution INTEGER
            )
            RETURNS BIGINT
            LANGUAGE plpython3u
            AS $$
span_price = max(0.0, price_max - price_min)
span_size = max(0.0, size_max - size_min)
p = max(1, int(price_resolution))
s = max(1, int(size_resolution))
# simple, fast estimate curve used for tiny sampling checks
mult = 1.0 + min(2.0, span_price / 10000.0) * 0.05 + min(2.0, span_size / 100000.0) * 0.05
return int(max(1, p * s * mult))
            $$;
        $fn$;
    ELSE
        RAISE NOTICE 'plpython3u function not created because extension is unavailable.';
    END IF;
END $$;
