import React from "react";
import { CircleUserRound, Settings2 } from "lucide-react";
import styles from "../styles/TopNav.module.css";

export default function TopNav() {
    return (
        <div className={styles.topNav}>
            <div className={styles.brandBlock}>
                <h1>AlgoSolver</h1>
                <span>Kinetic Precisionist</span>
            </div>

            <nav className={styles.topTabs}>
                <button className={styles.topTabActive} type="button">Generation</button>
                <button className={styles.topTab} type="button">Solver</button>
                <button className={styles.topTab} type="button">Database</button>
            </nav>

            <div className={styles.topActions}>
                <button className={styles.topIconButton} type="button" aria-label="Settings">
                    <Settings2 size={15} />
                </button>
                <button className={styles.topIconButton} type="button" aria-label="Profile">
                    <CircleUserRound size={15} />
                </button>
            </div>
        </div>
    );
}
