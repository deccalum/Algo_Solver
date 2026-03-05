import { useState } from "react";
import styles from "../styles/PageHeader.module.css";

export default function PageHeader({ tabs, activeTab, onTabChange }) {
    return (
        <header className={styles.header}>
            <div className={styles.titleSection}>
                <h1 className={styles.title}>Algo Solver</h1>
            </div>

            <nav className={styles.tabBar}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ""}`}
                        onClick={() => onTabChange(tab.id)}
                        title={tab.description}
                    >
                        {tab.icon && <span className={styles.tabIcon}>{tab.icon}</span>}
                        <span className={styles.tabLabel}>{tab.label}</span>
                    </button>
                ))}
            </nav>

            <div className={styles.headerSpacer} />
        </header>
    );
}
