export default function GlobalControls({ model, setModel }) {
    return (
      <div>
        <h3>Global Controls</h3>
  
        <label>Min Price</label>
        <input
          type="number"
          value={model.minPrice}
          onChange={(e) =>
            setModel({ ...model, minPrice: Number(e.target.value) })
          }
        />
  
        <label>Max Price</label>
        <input
          type="number"
          value={model.maxPrice}
          onChange={(e) =>
            setModel({ ...model, maxPrice: Number(e.target.value) })
          }
        />
  
        <label>Inflation</label>
        <input
          type="range"
          min="0.5"
          max="2"
          step="0.01"
          value={model.inflation}
          onChange={(e) =>
            setModel({ ...model, inflation: Number(e.target.value) })
          }
        />
      </div>
    );
  }
  