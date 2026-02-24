import { useState } from "react";
import { BigControl } from "./BigControl";
import styles from "../styles/Generation.module.css";

export default function RangeControl({
    label,
    minValue,
    maxValue,
    setMin,
    setMax,
    maxLimit,
    accent,
}) {
    const clampMin = (val) => {
        if (val >= maxValue) return;
        setMin(val);
    };

    const clampMax = (val) => {
        if (val <= minValue) return;
        setMax(val);
    };

    return (
        <div
            className={styles.rangePanel}
            style={{ backgroundColor: accent }}
        >
            <div className={styles.rangeHeader}>{label}</div>

            <div className={styles.rangeRow}>
                <BigControl
                    label="Min"
                    value={minValue}
                    setValue={clampMin}
                    max={maxLimit}
                    accent={accent}
                />

                <BigControl
                    label="Max"
                    value={maxValue}
                    setValue={clampMax}
                    max={maxLimit}
                    accent={accent}
                />
            </div>
        </div>
    );
}
