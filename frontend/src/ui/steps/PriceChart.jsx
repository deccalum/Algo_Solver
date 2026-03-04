import { useId } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Brush,
} from "recharts";

export default function PriceChart({
  data,
  zones,
  variant = "price",
  xMin,
  xMax,
  zonesArePercent = false,
  zoomable = false,
}) {
  const instanceId = useId().replace(/[:]/g, "");
  const safeData =
    Array.isArray(data) && data.length
      ? data
      : [
          { x: 0, y: 0 },
          { x: 25, y: 12 },
          { x: 50, y: 18 },
          { x: 75, y: 22 },
          { x: 100, y: 28 },
        ];
  const dataXValues = safeData.map((point) => point.x).filter(Number.isFinite);
  const fallbackMin = dataXValues.length ? Math.min(...dataXValues) : 0;
  const fallbackMax = dataXValues.length ? Math.max(...dataXValues) : 100;
  const domainMin = Number.isFinite(xMin) ? Number(xMin) : fallbackMin;
  const domainMax = Number.isFinite(xMax) ? Number(xMax) : fallbackMax;
  const safeDomain =
    domainMin <= domainMax ? [domainMin, domainMax] : [domainMax, domainMin];
  const [resolvedMin, resolvedMax] = safeDomain;
  const domainSpan = Math.max(1e-9, resolvedMax - resolvedMin);

  const safeZones = (Array.isArray(zones) ? zones : [])
    .map(Number)
    .filter(Number.isFinite)
    .map((zone) =>
      zonesArePercent
        ? resolvedMin + (Math.max(0, Math.min(100, zone)) / 100) * domainSpan
        : zone,
    )
    .filter((zone) => zone >= resolvedMin && zone <= resolvedMax);

  const strokeId = `chart-stroke-${variant}-${instanceId}`;
  const fillId = `chart-fill-${variant}-${instanceId}`;

  const strokeStart = variant === "size" ? "#70f2de" : "#8c7cff";
  const strokeEnd = variant === "size" ? "#46d9e6" : "#f08ad2";
  const fillBase = variant === "size" ? "#55d6cf" : "#b582ff";

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={safeData}>
        <defs>
          <linearGradient id={strokeId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={strokeStart} />
            <stop offset="100%" stopColor={strokeEnd} />
          </linearGradient>

          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fillBase} stopOpacity={0.25} />
            <stop offset="100%" stopColor={fillBase} stopOpacity={0.0} />
          </linearGradient>
        </defs>

        <CartesianGrid
          stroke="rgba(255, 255, 255, 0.15)"
          strokeDasharray="2 3"
          vertical
          horizontal
        />
        <XAxis
          dataKey="x"
          type="number"
          domain={safeDomain}
          tickCount={10}
          stroke="#94a3b8"
        />
        <YAxis stroke="#94a3b8" tickCount={8} />
        <Tooltip />

        {safeZones.map((zone, index) => (
          <ReferenceLine
            key={`zone-${variant}-${index}-${zone.toFixed(4)}`}
            x={zone}
            stroke="rgba(188, 196, 238, 0.35)"
            strokeDasharray="3 3"
          />
        ))}

        <Area
          type="monotone"
          dataKey="y"
          stroke={`url(#${strokeId})`}
          fill={`url(#${fillId})`}
          strokeWidth={1.5}
          isAnimationActive={false}
        />

        {zoomable && (
          <Brush
            dataKey="x"
            height={12}
            stroke={strokeStart}
            travellerWidth={8}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
