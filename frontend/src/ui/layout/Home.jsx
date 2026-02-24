import styles from "../styles/Home.module.css";

export default function Home() {
    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>Cartesian Product Enumeration</h1>

                <p className={styles.subtitle}>Parametric Pricing & Product Generator</p>
                <p className={styles.subtitle}>Solver for combinatorial optimization problems</p>

                <div className={styles.buttonGroup}>
                    <button
                        className={styles.primaryButton}
                        onClick={() => {
                            const url = `${window.location.origin}${window.location.pathname}?main=true`;
                            window.location.href = url;
                        }}
                    >
                        Start
                    </button>
                    <button className={styles.secondaryButton}>Load</button>
                    <button className={styles.secondaryButton}>Import</button>
                </div>

                <div className={styles.info}>
                    <p>Status: Idle</p>
                    <p>Last Loaded: None</p>
                </div>
            </div>
        </div>
    );
}
