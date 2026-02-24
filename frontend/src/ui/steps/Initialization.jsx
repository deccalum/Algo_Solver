import { useRef, useState, useEffect } from "react";
import styles from "../styles/Initialization.module.css";
import { BigControl } from "../controls/BigControl";

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("en-US");
}

export default function InitializationControls({ onClose }) {
    const [budget, setBudget] = useState(100000);
    const [space, setSpace] = useState(1000);

    useEffect(() => {
    }, []);

    const close = onClose
        ? onClose
        : () => {
            const url = `${window.location.origin}${window.location.pathname}`;
            window.location.href = url;
        };

    function handleInitialize() {
        const payload = { budget, space };
        console.log("Initialize with", payload);
        close();
    }

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h2 className={styles.title}>Initialization</h2>

                <div className={styles.primaryRow}>
                    <BigControl label="Budget" value={budget} setValue={setBudget} max={1_000_000} accent="#0f172a" />
                    <BigControl label="Space (m³)" value={space} setValue={setSpace} max={10_000} accent="#211b37" />
                </div>

                <div className={styles.secondaryRow}>
                    <div className={styles.bigControl} style={{ borderColor: "#7c3aed" }}>
                        <div className={styles.bigLabel}>Preview</div>
                        <div className={styles.placeholderBox} />
                    </div>

                    <div className={styles.bigControl} style={{ borderColor: "#b91c1c" }}>
                        <div className={styles.bigLabel}>Advanced</div>
                        <div className={styles.placeholderBox} />
                    </div>
                </div>

                <div className={styles.footer}>
                    <button className={styles.backButton} onClick={close}>
                        Back
                    </button>
                    <button className={styles.confirmButton} onClick={
                        function handleConfirm() {
                            document.getElementById("generation-section")?.scrollIntoView({ behavior: "smooth" });
                        }
                    }>
                        Confirm
                    </button>
                </div>
            </div>
        </div>
    );
}
