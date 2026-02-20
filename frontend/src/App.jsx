import { useState, useMemo } from "react";
import GlobalControls from "./components/GlobalControls";
import ZonePanel from "./components/ZonePanel";
import PriceChart from "./components/PriceChart";
import { generatePrices } from "./model/generatePrices";

export default function App() {
  const [model, setModel] = useState({
    minPrice: 1,
    maxPrice: 5000,
    inflation: 1,
    zones: [
      {
        id: crypto.randomUUID(),
        spanShare: 1,
        resolution: 10,
        mode: "power",
        bias: 1,
        step: 1,
      },
    ],
  });

  const prices = useMemo(() => {
    return generatePrices(model);
  }, [model]);

  return (
    <div style={{ display: "flex", padding: 20 }}>
      <div style={{ width: 350 }}>
        <GlobalControls model={model} setModel={setModel} />
        <ZonePanel model={model} setModel={setModel} />
      </div>

      <div style={{ flex: 1 }}>
        <PriceChart prices={prices} />
      </div>
    </div>
  );
}
  