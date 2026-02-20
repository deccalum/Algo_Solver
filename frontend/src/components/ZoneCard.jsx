export default function ZoneCard({ zone, model, setModel }) {
  const updateZone = (changes) => {
    setModel({
      ...model,
      zones: model.zones.map((existingZone) =>
        existingZone.id === zone.id ? { ...existingZone, ...changes } : existingZone
      ),
    });
  };

  return (
    <div style={{ border: "1px solid #ccc", padding: 10, marginBottom: 10 }}>
      <label>Span Share</label>
      <input
        type="range"
        min="0.1"
        max="5"
        step="0.1"
        value={zone.spanShare}
        onChange={(e) => updateZone({ spanShare: Number(e.target.value) })}
      />

      <label>Resolution</label>
      <input
        type="number"
        value={zone.resolution}
        onChange={(e) => updateZone({ resolution: Number(e.target.value) })}
      />

      <label>Mode</label>
      <select value={zone.mode} onChange={(e) => updateZone({ mode: e.target.value })}>
        <option value="power">Power</option>
        <option value="s-curve">S-Curve</option>
        <option value="exponential">Exponential</option>
        <option value="exact">Exact</option>
      </select>

      {zone.mode !== "exact" && (
        <>
          <label>Bias</label>
          <input
            type="range"
            min="0.1"
            max="5"
            step="0.1"
            value={zone.bias}
            onChange={(e) => updateZone({ bias: Number(e.target.value) })}
          />
        </>
      )}

      {zone.mode === "exact" && (
        <>
          <label>Step</label>
          <input
            type="number"
            value={zone.step}
            onChange={(e) => updateZone({ step: Number(e.target.value) })}
          />
        </>
      )}
    </div>
  );
}
