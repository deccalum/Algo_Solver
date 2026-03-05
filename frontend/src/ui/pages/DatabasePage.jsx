import { useState, useEffect } from "react";
import { ChevronDown, RotateCw, Download } from "lucide-react";
import styles from "../styles/DatabasePage.module.css";

async function fetchTables() {
    try {
        const response = await fetch("http://localhost:8080/api/database/tables");
        if (!response.ok) throw new Error("Failed to fetch tables");
        return await response.json();
    } catch (error) {
        console.error("Error fetching tables:", error);
        return [];
    }
}

async function fetchTableData(tableName) {
    try {
        const response = await fetch(
            `http://localhost:8080/api/database/tables/${tableName}/data`
        );
        if (!response.ok) throw new Error(`Failed to fetch data for ${tableName}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching data for ${tableName}:`, error);
        return [];
    }
}

async function fetchTableSchema(tableName) {
    try {
        const response = await fetch(
            `http://localhost:8080/api/database/tables/${tableName}/schema`
        );
        if (!response.ok) throw new Error(`Failed to fetch schema for ${tableName}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching schema for ${tableName}:`, error);
        return [];
    }
}

export default function DatabasePage() {
    const [tables, setTables] = useState([]);
    const [expandedTable, setExpandedTable] = useState(null);
    const [tableData, setTableData] = useState({});
    const [tableSchemas, setTableSchemas] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadTables();
    }, []);

    const loadTables = async () => {
        setLoading(true);
        setError(null);
        const fetchedTables = await fetchTables();
        setTables(fetchedTables);
        setLoading(false);
    };

    const toggleTable = async (tableName) => {
        if (expandedTable === tableName) {
            setExpandedTable(null);
        } else {
            setExpandedTable(tableName);
            if (!tableData[tableName]) {
                const [data, schema] = await Promise.all([
                    fetchTableData(tableName),
                    fetchTableSchema(tableName),
                ]);
                setTableData((prev) => ({ ...prev, [tableName]: data }));
                setTableSchemas((prev) => ({ ...prev, [tableName]: schema }));
            }
        }
    };

    const downloadTableAsCSV = (tableName) => {
        const data = tableData[tableName] || [];
        const schema = tableSchemas[tableName] || [];
        if (!data.length) return;

        const columns = schema.map((col) => col.name);
        const csv = [
            columns.join(","),
            ...data.map((row) => columns.map((col) => JSON.stringify(row[col])).join(",")),
        ].join("\n");

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${tableName}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    return (
        <main className={styles.container}>
            <div className={styles.header}>
                <h2>Database Tables</h2>
                <button
                    className={styles.refreshButton}
                    onClick={loadTables}
                    disabled={loading}
                    title="Refresh tables"
                >
                    <RotateCw size={18} />
                </button>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            <div className={styles.tablesList}>
                {loading && <p className={styles.loading}>Loading tables...</p>}

                {tables.length === 0 && !loading && (
                    <p className={styles.emptyState}>
                        No tables found. Make sure the backend is running on
                        http://localhost:8080
                    </p>
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
                            <span className={styles.rowCount}>
                                {table.row_count} rows
                            </span>
                        </button>

                        {expandedTable === table.name && (
                            <div className={styles.tableContent}>
                                <div className={styles.tableToolbar}>
                                    <button
                                        className={styles.downloadButton}
                                        onClick={() => downloadTableAsCSV(table.name)}
                                        title="Download as CSV"
                                    >
                                        <Download size={16} />
                                        Export CSV
                                    </button>
                                </div>

                                <div className={styles.tableWrapper}>
                                    <table className={styles.table}>
                                        <thead>
                                            <tr>
                                                {(tableSchemas[table.name] || []).map((col) => (
                                                    <th key={col.name} className={styles.columnHeader}>
                                                        {col.name}
                                                        <span className={styles.columnType}>
                                                            {col.type}
                                                        </span>
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(tableData[table.name] || []).map((row, idx) => (
                                                <tr key={idx} className={styles.tableRow}>
                                                    {(tableSchemas[table.name] || []).map((col) => (
                                                        <td key={col.name} className={styles.tableCell}>
                                                            {formatCellValue(row[col.name])}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {(tableData[table.name]?.length || 0) === 0 && (
                                    <p className={styles.noData}>No data in this table</p>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </main>
    );
}

function formatCellValue(value) {
    if (value === null || value === undefined) {
        return <span className="null">NULL</span>;
    }
    if (typeof value === "boolean") {
        return value ? "true" : "false";
    }
    if (typeof value === "object") {
        return JSON.stringify(value);
    }
    return String(value);
}
