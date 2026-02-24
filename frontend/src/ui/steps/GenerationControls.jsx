import { useState } from "react";
import RangeControl from "../controls/RangeControl";
import { BigControl } from "../controls/BigControl";
import { SmallControl } from "../controls/SmallControl";
import styles from "../styles/Generation.module.css";

export default function GenerationControls() {
    const [priceMin, setPriceMin] = useState(1);
    const [priceMax, setPriceMax] = useState(10000);

    const [sizeMin, setSizeMin] = useState(0.1);
    const [sizeMax, setSizeMax] = useState(100000);

    const [logisticsOptimal, setLogisticsOptimal] =
        useState(2000);

    const [logisticsBaseCost, setLogisticsBaseCost] =
        useState(0.5);

    return (
        <div className={styles.container}>
            <h2>Product Generation</h2>

            <RangeControl
                label="Price Range"
                minValue={priceMin}
                maxValue={priceMax}
                setMin={setPriceMin}
                setMax={setPriceMax}
                maxLimit={100000}
                accent="#1e293b"
            />

            <RangeControl
                label="Size Range"
                minValue={sizeMin}
                maxValue={sizeMax}
                setMin={setSizeMin}
                setMax={setSizeMax}
                maxLimit={200000}
                accent="#065f46"
            />

            <SmallControl
                label="Logistics Optimal"
                value={logisticsOptimal}
                setValue={setLogisticsOptimal}
                max={100000}
                accent="#7c3aed"
            />

            <SmallControl
                label="Logistics Base Cost"
                value={logisticsBaseCost}
                setValue={setLogisticsBaseCost}
                max={10}
                accent="#b91c1c"
            />
        </div>
    );
}
