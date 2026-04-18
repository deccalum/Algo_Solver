# Infinite Row Model (!Not in use currently)
To safely browse tables with millions of rows, this project uses server-side pagination across Python and React so only a 100-row block is fetched at a time.

## Why
Sending entire tables as JSON will exhaust browser memory and can trigger backend OOM failures.

## 1) Python (FastAPI + SQLAlchemy)
File: `python/server/api.py`

- Endpoint: `GET /api/database/tables/{name}/data`
- Params: `limit`, `offset`, and optional `filters`
- Query: `LIMIT :limit OFFSET :offset`

Implementation notes:

- Uses SQLAlchemy `create_engine` + `text(...)`.
- Validates table names before interpolation to avoid SQL injection.
- Parses AG Grid `filterModel` from `filters` JSON.
- Converts supported text/number filters into SQL `WHERE` clauses with bound params.
- Returns rows as list-of-dicts via `result.mappings().all()`.

## 2) React + AG Grid Infinite Row Model
File: `frontend/src/ui/pages/DatabasePage.jsx`

Grid configuration:

- `rowModelType="infinite"`
- `cacheBlockSize={100}`
- `maxBlocksInCache={1}`
- `maxConcurrentDatasourceRequests={1}`

Datasource behavior:

- On scroll, AG Grid requests `startRow` and `endRow`.
- Frontend calls:
  - `/api/database/tables/{table}/data?limit=${endRow-startRow}&offset=${startRow}&filters=${JSON.stringify(filterModel)}`
- If fewer rows are returned than requested, datasource reports `lastRow`.

## Server-Side Filtering
Filtering is executed in PostgreSQL for scale.

- AG Grid emits `filterModel` in each datasource request.
- Frontend serializes this model as `filters` query string JSON.
- Java forwards `filters` unchanged.
- Python parses `filters` and builds `WHERE` with bound values.

Supported operators:

- Text: `contains`, `notContains`, `startsWith`, `endsWith`, `equals`.
- Number: `equals`, `notEqual`, `greaterThan`, `greaterThanOrEqual`, `lessThan`, `lessThanOrEqual`, `inRange`.

## Result
With this setup, the app avoids loading full tables into memory and scales to very large row counts while staying responsive.
