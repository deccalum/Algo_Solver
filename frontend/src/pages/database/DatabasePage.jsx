import React, { useState, useEffect, useMemo } from 'react';
import { getTables, getTableSchema, getTableData } from '../../api/client';
import { Icon } from '../../components/shared/Icon';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import '../../styles/database-page.css';

function TableList({ tables, selected, onSelect }) {
  return (
    <aside className="db-page__table-list">
      <div className="db-page__table-list-header">
        <span className="db-page__table-list-title">TABLES</span>
      </div>
      <nav className="db-page__table-list-nav">
        {tables.map(t => (
          <button
            key={t.name}
            className={`db-page__table-list-btn ${
              selected === t.name
                ? 'db-page__table-list-btn--active'
                : 'db-page__table-list-btn--inactive'
            }`}
            onClick={() => onSelect(t.name)}
          >
            <span className="db-page__table-list-name">{t.name}</span>
            <span className="db-page__table-list-count">
              {t.row_count.toLocaleString()}
            </span>
          </button>
        ))}
      </nav>
    </aside>
  );
}

function SchemaPanel({ schema }) {
  if (!schema || schema.length === 0) return null;
  return (
    <div className="db-page__schema">
      <div className="db-page__schema-title">SCHEMA</div>
      <div className="db-page__schema-badges">
        {schema.map(col => (
          <span key={col.column} className="db-page__schema-badge">
            {col.column} <span className="db-page__schema-badge-type">{col.type}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function formatCell(value) {
  if (value == null) return '—';
  if (typeof value === 'object') return JSON.stringify(value).slice(0, 100);
  return String(value);
}

function SimpleDataTable({ data, schema }) {
  if (!data || !data.data || data.data.length === 0) return null;
  const columns = schema?.map(c => c.column) || Object.keys(data.data[0]);
  return (
    <div className="db-page__simple-table-wrap">
      <table className="db-page__simple-table">
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.data.map((row, i) => (
            <tr key={i} className={i % 2 !== 0 ? 'db-page__simple-table-row--striped' : ''}>
              {columns.map(col => (
                <td key={col}>{formatCell(row[col])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DatabasePage() {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [schema, setSchema] = useState([]);
  const [tableDataPreview, setTableDataPreview] = useState(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [loading, setLoading] = useState(true);
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
      setTables(await getTables());
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
      const result = await fetch('/api/pipeline/run-dev', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!result.ok) throw new Error(`Pipeline failed: ${result.status}`);
      const data = await result.json();
      setRunStatus({
        ok: true,
        message: `Pipeline finished. Objective: ${data.objective_value?.toFixed(4) || "N/A"}`,
      });
      setTableErrors({});
      setGridApis({});
      setSelectedTable(null);
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

  const getColumnDefs = (tableSchema) => {
    if (!tableSchema || tableSchema.length === 0) return [];
    return tableSchema.map((col) => ({
      field: col.column,
      headerName: `${col.column} (${col.type})`,
      valueFormatter: (params) => {
        if (params.value == null) return 'NULL';
        if (typeof params.value === 'boolean') return params.value ? 'true' : 'false';
        if (typeof params.value === 'object') return JSON.stringify(params.value);
        return String(params.value);
      },
    }));
  };

  const onGridReady = (params, tableName) => {
    console.debug('onGridReady', { tableName, schemaLength: schema?.length });
    setGridApis((prev) => ({ ...prev, [tableName]: params.api }));

    const dataSource = {
      getRows: async (request) => {
        try {
          const { startRow, endRow, filterModel } = request;
          const limit = Math.max(endRow - startRow, 1);

          console.debug('datasource.getRows', { tableName, startRow, endRow, limit, filterModel });

          const searchParams = new URLSearchParams({
            limit: String(limit),
            offset: String(startRow),
          });

          if (filterModel && Object.keys(filterModel).length > 0) {
            searchParams.set('filters', JSON.stringify(filterModel));
          }

          const data = await getTableData(tableName, limit, startRow, searchParams.get('filters'));
          console.debug('datasource.getRows: fetched', { total: data?.total, rows: data?.data?.length });

          const lastRow = typeof data?.total === 'number'
            ? data.total
            : (data.data.length < limit ? startRow + data.data.length : -1);

          request.successCallback(data.data, lastRow);
        } catch (e) {
          console.error('datasource.getRows error', e);
          request.failCallback();
        }
      },
    };

    if (typeof params.api.setDatasource === 'function') {
      params.api.setDatasource(dataSource);
    } else if (typeof params.api.setGridOption === 'function') {
      params.api.setGridOption('datasource', dataSource);
    }
  };

  useEffect(() => {
    if (!selectedTable) return;
    setSchemaLoading(true);
    getTableSchema(selectedTable).then((s) => {
      setSchema(s);
      setSchemaLoading(false);
    }).catch(() => {
      setSchema([]);
      setSchemaLoading(false);
    });
  }, [selectedTable]);

  useEffect(() => {
    if (!selectedTable) {
      setTableDataPreview(null);
      return;
    }
    setTableDataPreview(null);
    getTableData(selectedTable, 10, 0).then((d) => {
      console.debug('preview rows fetched', { table: selectedTable, rows: d?.data?.length });
      setTableDataPreview(d);
    }).catch((e) => {
      console.error('preview fetch failed', e);
      setTableDataPreview(null);
    });
  }, [selectedTable, schema]);

  if (loading) {
    return (
      <div className="db-page--loading">
        <div className="db-page__loading-text">Loading tables...</div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="db-page">
        <div className="db-page__header">
          <h2 className="db-page__title">DATABASE BROWSER</h2>
          <div className="db-page__actions">
            <button
              className="db-page__action-btn"
              onClick={runDevPipeline}
              disabled={running}
            >
              {running ? 'Running…' : 'Run Dev Pipeline'}
            </button>
            <button
              className="db-page__action-btn"
              onClick={loadTables}
              disabled={loading}
            >
              Refresh
            </button>
            <span className="db-page__table-count">{tables.length} tables</span>
          </div>
        </div>

        {runStatus && (
          <div className={`db-page__status ${runStatus.ok ? 'db-page__status--success' : 'db-page__status--error'}`}>
            {runStatus.message}
          </div>
        )}
        {error && (
          <div className="db-page__status db-page__status--error">{error}</div>
        )}

        <div className="db-page__body">
          <TableList tables={tables} selected={selectedTable} onSelect={setSelectedTable} />

          <div className="db-page__content">
            {!selectedTable ? (
              <div className="db-page__empty">
                <Icon name="table_chart" className="db-page__empty-icon" />
                <p className="db-page__empty-title">Select a table</p>
                <p className="db-page__empty-subtitle">Choose a table from the left to browse its data</p>
              </div>
            ) : (
              <div className="db-page__detail">
                <div className="db-page__detail-header">
                  <span className="db-page__detail-name">{selectedTable}</span>
                  <div className="db-page__detail-actions">
                    <button
                      className="db-page__action-btn"
                      onClick={() => downloadCSV(selectedTable)}
                    >
                      Export CSV
                    </button>
                    <span className="db-page__detail-rows">
                      {tables.find(t => t.name === selectedTable)?.row_count?.toLocaleString() || 0} rows
                    </span>
                  </div>
                </div>
                <div className="db-page__detail-body">
                  <SchemaPanel schema={schema} />
                </div>
                {schemaLoading ? (
                  <div className="db-page__detail-status">Loading schema...</div>
                ) : schema.length === 0 ? (
                  <div className="db-page__detail-status">No schema available</div>
                ) : (
                  <div className="ag-theme-alpine db-page__grid-container">
                    {tableDataPreview && <SimpleDataTable data={tableDataPreview} schema={schema} />}
                    <AgGridReact
                      key={selectedTable}
                      columnDefs={getColumnDefs(schema)}
                      defaultColDef={defaultColDef}
                      rowModelType="infinite"
                      cacheBlockSize={100}
                      maxBlocksInCache={1}
                      maxConcurrentDatasourceRequests={1}
                      onGridReady={(params) => onGridReady(params, selectedTable)}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
    this.setState({ info });
  }

  render() {
    if (this.state.error) {
      return (
        <div className="db-page__error-boundary">
          <div className="db-page__error-card">
            <div className="db-page__error-title">An error occurred rendering Database page</div>
            <div className="db-page__error-message">
              {String(this.state.error && this.state.error.toString())}
            </div>
            {this.state.info && (
              <pre className="db-page__error-stack">{this.state.info.componentStack}</pre>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
