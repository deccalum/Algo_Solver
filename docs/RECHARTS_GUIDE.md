# Recharts Guide (Algo_Solver)

This guide explains:
- how Recharts works in React,
- how to wire chart data to your app state,
- how to add/remove zones,
- how to link variables across controls and charts,
- and how to customize charts broadly.

## Official References

- Recharts home: https://recharts.github.io
- Getting started: https://recharts.github.io/en-US/guide/getting-started/
- Installation: https://recharts.github.io/en-US/guide/installation/
- API docs: https://recharts.github.io/en-US/api
- Examples: https://recharts.github.io/en-US/examples
- Storybook: https://recharts.github.io/en-US/storybook/
- Wiki home: https://github.com/recharts/recharts/wiki
- Wiki: Axis domains and ticks: https://github.com/recharts/recharts/wiki/Axis-domains-and-ticks
- Wiki: Tooltip event type and shared prop: https://github.com/recharts/recharts/wiki/Tooltip-event-type-and-shared-prop
- Wiki: 3.0 migration guide: https://github.com/recharts/recharts/wiki/3.0-migration-guide

## Mental Model

Recharts is a set of composable React components.

- `ResponsiveContainer` gives auto sizing.
- A chart container (`AreaChart`, `LineChart`, `BarChart`, etc.) receives `data`.
- Child components (`XAxis`, `YAxis`, `Area`, `Tooltip`, `ReferenceLine`, etc.) define rendering behavior.
- You customize via props and optional custom renderers.

In this repo, chart usage is in:
- [frontend/src/ui/steps/PriceChart.jsx](../frontend/src/ui/steps/PriceChart.jsx)
- [frontend/src/ui/layout/MainPage.jsx](../frontend/src/ui/layout/MainPage.jsx)

## Basic Setup Pattern

```jsx
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function MyChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data}>
        <CartesianGrid stroke="rgba(255,255,255,0.15)" />
        <XAxis dataKey="x" />
        <YAxis />
        <Tooltip />
        <Area type="monotone" dataKey="y" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

## Add / Remove Zones (State + UI + Chart)

### 1) Keep zones in React state

```jsx
const [zones, setZones] = useState([20, 45, 70]);
```

### 2) Add/remove/update zone actions

```jsx
const addZone = () => {
  setZones((prev) => [...prev, Math.min(100, (prev[prev.length - 1] ?? 0) + 10)]);
};

const removeZone = (index) => {
  setZones((prev) => prev.filter((_, i) => i !== index));
};

const updateZone = (index, value) => {
  setZones((prev) => prev.map((z, i) => (i === index ? value : z)));
};
```

### 3) Render zones as visual markers in Recharts

```jsx
{zones.map((zone, i) => (
  <ReferenceLine
    key={`zone-${i}`}
    x={zone}
    stroke="rgba(255,255,255,0.25)"
    strokeDasharray="3 3"
  />
))}
```

### 4) Keep zones sorted and unique (recommended)

```jsx
const normalizeZones = (arr) => [...new Set(arr)].sort((a, b) => a - b);
```

Use this before writing back to state when users can edit zone values directly.

## Link Variables Across Controls and Chart

You already do this pattern in `MainPage.jsx` with state variables for ranges/zones.

### Recommended flow

1. Controls update local React state (`setPriceMin`, `setPriceMax`, `setPriceZones`, etc.).
2. Derived data is computed with `useMemo`.
3. Chart receives only the final props (`data`, `zones`, style variant).

```jsx
const filteredData = useMemo(() => {
  return rawData.filter((p) => p.x >= priceMin && p.x <= priceMax);
}, [rawData, priceMin, priceMax]);

<PriceChart data={filteredData} zones={zones} variant="price" />
```

### Single source of truth rule

Avoid duplicate state for the same value in multiple places.
- Good: one `zones` state passed down.
- Risky: separate chart zones and panel zones not synced.

## Broad Customization Options

## 1) Theme / colors

- Use gradients in `<defs>` (already in `PriceChart.jsx`).
- Use `stroke`, `fill`, `strokeOpacity`, `strokeWidth` per series.
- Keep palette in constants for consistency.

## 2) Axes and domain

- `XAxis`/`YAxis` support domain and ticks.
- For fixed range:

```jsx
<XAxis dataKey="x" type="number" domain={[0, 100]} />
<YAxis type="number" domain={[0, 'auto']} />
```

See wiki topic “Axis domains and ticks”.

## 3) Tooltip behavior

- Add `<Tooltip />` for hover readout.
- Customize with `formatter`, `labelFormatter`, or custom content component.
- For multi-series behavior, see wiki topic “Tooltip event type and shared prop”.

## 4) Grid and markers

- `CartesianGrid` for readability.
- `ReferenceLine`, `ReferenceArea`, `ReferenceDot` for thresholds and zones.

## 5) Animation / performance

- Disable animation for very large data:

```jsx
<Area isAnimationActive={false} />
```

- Memoize transformed data with `useMemo`.
- Keep chart props stable when possible.

## 6) Accessibility

- Keep axis labels and sufficient contrast.
- Prefer meaningful legends/tooltips.
- See wiki “Recharts and accessibility”.

## Repo-Specific Notes

1. `PriceChart.jsx` currently imports `Tooltip` and `ReferenceLine` but does not render them yet.
   - If you want visible zone separators, render `ReferenceLine` for each zone.

2. If multiple charts render the same SVG gradient ID (`priceStroke`, `priceFill`) in one page, IDs can collide.
   - Safer approach: generate per-variant IDs (`priceStroke-price`, `priceStroke-size`) or pass an `idPrefix` prop.

3. Keep zone arrays numeric and validated before chart rendering:

```jsx
const safeZones = Array.isArray(zones) ? zones.filter(Number.isFinite) : [];
```

## Suggested Integration Checklist

- [ ] Install/import Recharts components needed per chart type.
- [ ] Keep chart inputs in state (`data`, `zones`, ranges).
- [ ] Derive transformed chart data with `useMemo`.
- [ ] Render chart primitives (`XAxis`, `YAxis`, series, tooltip, markers).
- [ ] Add zone actions (add/remove/update) and keep zones normalized.
- [ ] Keep style IDs unique when rendering multiple charts.
- [ ] Validate behavior with both normal and empty datasets.

## Quick Example: Zones in Current `PriceChart`

```jsx
<CartesianGrid stroke="rgba(255, 255, 255, 0.15)" />
<XAxis dataKey="x" stroke="#94a3b8" />
<YAxis stroke="#94a3b8" />
<Tooltip />

{safeZones.map((zone, index) => (
  <ReferenceLine
    key={`zone-${index}`}
    x={zone}
    stroke="rgba(201, 209, 255, 0.3)"
    strokeDasharray="3 3"
  />
))}

<Area
  type="monotone"
  dataKey="y"
  stroke={`url(#${strokeId})`}
  fill={`url(#${fillId})`}
  strokeWidth={1.5}
/>
```

---
If you want, the next step can be a direct implementation pass that wires `zones` into visible `ReferenceLine`s and adds unique gradient IDs in `PriceChart.jsx`.
