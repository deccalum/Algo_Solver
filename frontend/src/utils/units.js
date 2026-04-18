// units.js — smart display formatting for physical quantities.
// Backend stores in base units: kg, m³, $ — this file converts to human-readable.

/** Format a weight in kg with automatic unit scaling. */
export function formatWeight(kg, decimals) {
  if (kg == null || isNaN(kg)) return '—';
  const abs = Math.abs(kg);
  if (abs === 0) return `0 kg`;
  if (abs < 0.001)  { const d = decimals ?? 1; return `${(kg * 1e6).toFixed(d)} mg`; }
  if (abs < 1)      { const d = decimals ?? 1; return `${(kg * 1000).toFixed(d)} g`; }
  if (abs < 1000)   { const d = decimals ?? 2; return `${kg.toFixed(d)} kg`; }
  return `${(kg / 1000).toFixed(decimals ?? 2)} t`;
}

/** Format a volume in m³ with automatic unit scaling. */
export function formatVolume(m3, decimals) {
  if (m3 == null || isNaN(m3)) return '—';
  const abs = Math.abs(m3);
  if (abs === 0) return `0 m³`;
  if (abs < 0.0001)  { const d = decimals ?? 0; return `${(m3 * 1e6).toFixed(d)} cm³`; }
  if (abs < 0.001)   { const d = decimals ?? 1; return `${(m3 * 1000).toFixed(d)} L`; }
  if (abs < 1)       { const d = decimals ?? 2; return `${(m3 * 1000).toFixed(d)} L`; }
  return `${m3.toFixed(decimals ?? 3)} m³`;
}

/** Format a price in dollars with compact notation for large values. */
export function formatPrice(usd, decimals) {
  if (usd == null || isNaN(usd)) return '—';
  const abs = Math.abs(usd);
  if (abs < 1)       return `$${usd.toFixed(2)}`;
  if (abs < 1000)    return `$${usd.toFixed(decimals ?? 0)}`;
  if (abs < 1e6)     return `$${(usd / 1000).toFixed(decimals ?? 1)}k`;
  if (abs < 1e9)     return `$${(usd / 1e6).toFixed(decimals ?? 1)}M`;
  return `$${(usd / 1e9).toFixed(1)}B`;
}

/** Format a demand count (integer units). */
export function formatDemand(v) {
  if (v == null) return '—';
  return `${Math.round(v)} units`;
}

/**
 * Format any param value by name. Falls back to plain number.
 * @param {number} value
 * @param {string} paramName  e.g. 'price', 'weight', 'volume'
 * @returns {string}
 */
export function formatParamValue(value, paramName) {
  if (value == null || isNaN(value)) return '—';
  switch (paramName) {
    case 'price':         return formatPrice(value);
    case 'weight':        return formatWeight(value);
    case 'volume':        return formatVolume(value);
    case 'demand':        return `${value} units`;
    case 'cost_per_watt': return `$${value.toFixed(2)}/W`;
    case 'labour_hours':  return `${value.toFixed(1)} h`;
    case 'efficiency':    return `${value.toFixed(1)}%`;
    case 'sunlight_hours':return `${value.toFixed(1)} h/day`;
    default:              return value.toFixed ? value.toFixed(3) : String(value);
  }
}
