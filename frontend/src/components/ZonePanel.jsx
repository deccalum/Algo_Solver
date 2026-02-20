import ZoneCard from "./ZoneCard";

export default function ZonePanel({ model, setModel }) {
  const addZone = () => {
    const newZone = {
      id: crypto.randomUUID(),
      spanShare: 1,
      resolution: 10,
      mode: "power",
      bias: 1,
      step: 1,
    };

    setModel({
      ...model,
      zones: [...model.zones, newZone],
    });
  };

  return (
    <div>
      <h3>Zones</h3>

      {model.zones.map((zone) => (
        <ZoneCard key={zone.id} zone={zone} model={model} setModel={setModel} />
      ))}

      <button onClick={addZone}>+ Add Zone</button>
    </div>
  );
}
