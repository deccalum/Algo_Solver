import { useRef, useState, useEffect } from "react";
import styles from "../styles/BigControl.module.css";

function formatNumber(value) {
    return Number(value ?? 0).toLocaleString("en-US");
}

export function BigControl({
    label,
    value,
    setValue,
    max = 1000000,
    accent = "#1e293b",
}) {
    const panelRef = useRef(null);
    const inputRef = useRef(null);

    const [active, setActive] = useState(false);
    const [editing, setEditing] = useState(false);
    const [tempValue, setTempValue] = useState(value);

    const dragState = useRef({
        dragging: false,
    });

    const startDrag = (e) => {
        if (editing) return;
        if (e.target.closest("button")) return;

        panelRef.current.requestPointerLock();
        dragState.current.dragging = true;
        setActive(true);
    };

    const handleMove = (e) => {
        if (!dragState.current.dragging) return;

        let sensitivity = max / 5000;

        if (e.shiftKey) sensitivity *= 0.25;

        let delta = e.movementX * sensitivity;

        let next = value + delta;

        if (e.ctrlKey) {
            const snapSize = max / 100;
            next = Math.round(next / snapSize) * snapSize;
        }

        setValue(
            Math.min(max, Math.max(0, Math.round(next)))
        );
    };

    const stopDrag = () => {
        if (!dragState.current.dragging) return;

        dragState.current.dragging = false;
        setActive(false);
        document.exitPointerLock();
    };

    useEffect(() => {
        document.addEventListener("mousemove", handleMove);
        document.addEventListener("mouseup", stopDrag);

        return () => {
            document.removeEventListener("mousemove", handleMove);
            document.removeEventListener("mouseup", stopDrag);
        };
    });

    const enterEditMode = () => {
        setEditing(true);
        setTempValue(value);

        setTimeout(() => {
            inputRef.current?.focus();
            inputRef.current?.select();
        }, 0);
    };

    const confirmEdit = () => {
        const parsed = Number(
            String(tempValue).replace(/,/g, "")
        );

        if (!isNaN(parsed)) {
            setValue(Math.min(max, Math.max(0, parsed)));
        }

        setEditing(false);
    };

    const cancelEdit = () => {
        setEditing(false);
    };

    const percent = Math.min((value / max) * 100, 100);

    return (
        <div
            ref={panelRef}
            className={`${styles.bigPanel} ${active ? styles.activePanel : ""
                }`}
            style={{ backgroundColor: accent }}
            onMouseDown={startDrag}
            onDoubleClick={enterEditMode}
        >
            <div className={styles.panelHeader}>{label}</div>

            <div className={styles.panelValue}>
                {editing ? (
                    <input
                        ref={inputRef}
                        value={tempValue}
                        onChange={(e) => setTempValue(e.target.value)}
                        onBlur={confirmEdit}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") confirmEdit();
                            if (e.key === "Escape") cancelEdit();
                        }}
                    />
                ) : (
                    formatNumber(value)
                )}
            </div>

            <div
                className={`${styles.gauge} ${active ? styles.activeGauge : ""
                    }`}
                style={{
                    width: `${percent}%`,
                    backgroundColor: "rgba(255,255,255,0.5)",
                }}
            />

            <div className={styles.panelDivider} />

            <div className={styles.multiplierRow}>
                <button>Mode A</button>
                <button>Mode B</button>
                <button>Mode C</button>
                <button>Mode D</button>
            </div>
        </div>
    );
}