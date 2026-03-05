import { useState } from "react";
import PageHeader from "../components/PageHeader";
import GenerationPage from "../pages/GenerationPage";
import SolverPage from "../pages/SolverPage";
import DatabasePage from "../pages/DatabasePage";
import styles from "../styles/AppLayout.module.css";

const TABS = [
    {
        id: "generation",
        label: "GENERATION",
        icon: "⚙️",
        description: "Configure generation parameters",
    },
    {
        id: "solver",
        label: "SOLVER",
        icon: "🔧",
        description: "Configure solver parameters",
    },
    {
        id: "database",
        label: "DATABASE",
        icon: "📊",
        description: "View and manage database tables",
    },
    {
        id: "empty1",
        label: "EMPTY",
        icon: "⬜",
        description: "Reserved for future use",
    },
    {
        id: "empty2",
        label: "EMPTY",
        icon: "⬜",
        description: "Reserved for future use",
    },
];

export default function AppLayout() {
    const [activeTab, setActiveTab] = useState("generation");

    const renderPage = () => {
        switch (activeTab) {
            case "generation":
                return <GenerationPage />;
            case "solver":
                return <SolverPage />;
            case "database":
                return <DatabasePage />;
            case "empty1":
            case "empty2":
                return (
                    <div style={{ flex: 1, padding: "2rem", textAlign: "center" }}>
                        <p style={{ color: "#9ca3af" }}>This section is reserved for future use</p>
                    </div>
                );
            default:
                return <GenerationPage />;
        }
    };

    return (
        <div className={styles.appContainer}>
            <PageHeader tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab} />
            <div className={styles.pageContainer}>
                {renderPage()}
            </div>
        </div>
    );
}
