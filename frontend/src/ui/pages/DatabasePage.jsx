import { useState, useEffect, useMemo } from "react";
import { ChevronDown, RotateCw, Download, Play } from "lucide-react";
import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css"; // Or ag-theme-quartz for v31+
import styles from "../styles/DatabasePage.module.css";

async function get(path) {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post(path, body = {}) {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export default function DatabasePage() {
  const [tables, setTables] = useState([]);
  const [expandedTable, setExpandedTable] = useState(null);
  const [tableSchemas, setTableSchemas] = useState({});
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [runStatus, setRunStatus] = useState(null);
  const [error, setError] = useState(null);
  const [tableErrors, setTableErrors] = useState({});
  const [gridApis, setGridApis] = useState({});

  const defaultColDef = useMemo(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      flex: 1,
      minWidth: 150,
    }),
    [],
  );

  useEffect(() => {
    loadTables();
  }, []);

  const loadTables = async () => {
    setLoading(true);
    setError(null);
    try {
      setTables(await get("/database/tables"));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const runDevPipeline = async () => {
    setRunning(true);
    setRunStatus(null);
    try {
      const result = await post("/pipeline/run-dev");
      setRunStatus({
        ok: true,
        message: `Pipeline finished. Objective: ${result.objective_value?.toFixed(4) || "N/A"}`,
      });
      setTableSchemas({});
      setTableErrors({});
      setGridApis({});
      setExpandedTable(null);
      await loadTables();
    } catch (e) {
      setRunStatus({ ok: false, message: e.message });
    } finally {
      setRunning(false);
    }
  };

  const downloadCSV = (tableName) => {
    const api = gridApis[tableName];
    if (!api) return;
    api.exportDataAsCsv({ fileName: `${tableName}.csv` });
  };

  const toggleTable = async (name) => {
    setExpandedTable((prev) => (prev === name ? null : name));

    if (!tableSchemas[name]) {
      try {
        const schema = await get(`/database/tables/${name}/schema`);
        setTableSchemas((prev) => ({ ...prev, [name]: schema }));
      } catch (e) {
        setTableErrors((prev) => ({ ...prev, [name]: e.message }));
      }
    }
  };

  const onGridReady = (params, tableName) => {
    setGridApis((prev) => ({ ...prev, [tableName]: params.api }));

    const dataSource = {
      getRows: async (request) => {
        try {
          const { startRow, endRow, filterModel } = request;
          const limit = Math.max(endRow - startRow, 1);

          const searchParams = new URLSearchParams({
            limit: String(limit),
            offset: String(startRow),
          });

          if (filterModel && Object.keys(filterModel).length > 0) {
            searchParams.set("filters", JSON.stringify(filterModel));
          }

          const data = await get(
            `/database/tables/${tableName}/data?${searchParams.toString()}`,
          );

          let lastRow = -1;
          if (data.length < limit) {
            lastRow = startRow + data.length;
          }

          request.successCallback(data, lastRow);
        } catch {
          request.failCallback();
        }
      },
    };

    params.api.setGridOption("datasource", dataSource);
  };

  // Maps dynamic schema to AG Grid column definitions
  const getColumnDefs = (tableName) => {
    const schema = tableSchemas[tableName] || [];
    return schema.map((col) => ({
      field: col.name,
      headerName: `${col.name} (${col.type})`,
      valueFormatter: (params) => {
        if (params.value == null) return "NULL";
        if (typeof params.value === "boolean")
          return params.value ? "true" : "false";
        if (typeof params.value === "object")
          return JSON.stringify(params.value);
        return String(params.value);
      },
    }));
  };

  return (
    <main className={styles.container}>
      <div className={styles.header}>
        <h2>Database</h2>
        <div className={styles.headerActions}>
          <button
            className={styles.runButton}
            onClick={runDevPipeline}
            disabled={running}
          >
            <Play size={16} /> {running ? "Running…" : "Run Dev Pipeline"}
          </button>
          <button
            className={styles.refreshButton}
            onClick={loadTables}
            disabled={loading}
          >
            <RotateCw size={18} />
          </button>
        </div>
      </div>

      {runStatus && (
        <div className={runStatus.ok ? styles.success : styles.error}>
          {runStatus.message}
        </div>
      )}
      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.tablesList}>
        {loading ? (
          <p>Loading…</p>
        ) : (
          tables.length === 0 && <p>No tables found.</p>
        )}

        {tables.map((table) => (
          <div key={table.name} className={styles.tableSection}>
            <button
              className={styles.tableHeader}
              onClick={() => toggleTable(table.name)}
            >
              <ChevronDown
                size={18}
                className={
                  expandedTable === table.name ? styles.chevronOpen : ""
                }
              />
              <span className={styles.tableName}>{table.name}</span>
              <span className={styles.rowCount}>{table.row_count} rows</span>
            </button>

            {expandedTable === table.name && (
              <div className={styles.tableContent}>
                {tableErrors[table.name] ? (
                  <div className={styles.error}>
                    Error: {tableErrors[table.name]}
                  </div>
                ) : (
                  <>
                    <button
                      className={styles.downloadButton}
                      onClick={() => downloadCSV(table.name)}
                    >
                      <Download size={16} /> Export CSV
                    </button>

                    <div
                      className="ag-theme-alpine-dark" // Matches your UI better
                      style={{ height: 600, width: "100%", marginTop: "1rem" }}
                    >
                      <AgGridReact
                        columnDefs={getColumnDefs(table.name)}
                        defaultColDef={defaultColDef}
                        rowModelType="infinite"
                        cacheBlockSize={100}
                        maxBlocksInCache={1}
                        maxConcurrentDatasourceRequests={1}
                        onGridReady={(params) =>
                          onGridReady(params, table.name)
                        }
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
