import { useEffect, useRef, useState } from "react";
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
  const timelineRef = useRef(null);
  const [activeDrag, setActiveDrag] = useState(null);

  const clampMin = (val) => {
    if (val >= maxValue) return;
    setMin(val);
  };

  const clampMax = (val) => {
    if (val <= minValue) return;
    setMax(val);
  };

  const numericLimit = Math.max(0, Number(maxLimit) || 0);
  const safeLimit = Math.max(1, numericLimit);

  useEffect(() => {
    if (!activeDrag) return;

    const htmlStyle = document.documentElement.style;
    const bodyStyle = document.body.style;
    const previousHtmlCursor = htmlStyle.cursor;
    const previousBodyCursor = bodyStyle.cursor;

    htmlStyle.setProperty("cursor", "none", "important");
    bodyStyle.setProperty("cursor", "none", "important");

    const handleMove = (event) => {
      const timeline = timelineRef.current;
      if (!timeline) return;

      const rect = timeline.getBoundingClientRect();
      if (!rect.width) return;

      const percent = Math.min(
        1,
        Math.max(0, (event.clientX - rect.left) / rect.width),
      );
      const nextValue = Math.round(percent * numericLimit);

      if (activeDrag === "min") {
        if (nextValue < maxValue) setMin(nextValue);
        return;
      }

      if (nextValue > minValue) setMax(nextValue);
    };

    const stopDrag = () => setActiveDrag(null);

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", stopDrag);

    return () => {
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", stopDrag);
      htmlStyle.cursor = previousHtmlCursor;
      bodyStyle.cursor = previousBodyCursor;
    };
  }, [activeDrag, maxValue, minValue, numericLimit, setMin, setMax]);

  const minPercent = Math.min(100, Math.max(0, (minValue / safeLimit) * 100));
  const maxPercent = Math.min(100, Math.max(0, (maxValue / safeLimit) * 100));
  const leftPercent = Math.min(minPercent, maxPercent);
  const rightPercent = Math.max(minPercent, maxPercent);

  return (
    <div className={styles.rangePanel} style={{ backgroundColor: accent }}>
      <div className={styles.rangeTopRow}>
        <div className={styles.rangeBound}>MIN</div>
        <div className={styles.rangeHeader}>{label}</div>
        <div className={styles.rangeBound}>MAX</div>
      </div>

      <div className={styles.rangeBottomRow}>
        <div className={styles.inlineValue}>
          {Number(minValue).toLocaleString("en-US")}
        </div>

        <div ref={timelineRef} className={styles.timelineInline}>
          <div className={styles.timelineTrack} />
          <div
            className={styles.timelineFill}
            style={{
              left: `${leftPercent}%`,
              width: `${rightPercent - leftPercent}%`,
            }}
          />
          <div
            className={styles.timelinePoint}
            style={{ left: `${minPercent}%` }}
            onMouseDown={(event) => {
              event.preventDefault();
              setActiveDrag("min");
            }}
          />
          <div
            className={styles.timelinePoint}
            style={{ left: `${maxPercent}%` }}
            onMouseDown={(event) => {
              event.preventDefault();
              setActiveDrag("max");
            }}
          />
        </div>

        <div className={styles.inlineValue}>
          {Number(maxValue).toLocaleString("en-US")}
        </div>
      </div>
    </div>
  );
}
