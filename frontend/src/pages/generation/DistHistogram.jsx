import '../../styles/dist-histogram.css';

// --- Math helpers ---

function stdNormPDF(x) {
  return Math.exp(-0.5 * x * x) / 2.506628274631;
}

function stdNormCDF(x) {
  if (x < -7) return 0;
  if (x > 7)  return 1;
  const k = 1 / (1 + 0.2316419 * Math.abs(x));
  const p = ((((1.330274429*k - 1.821255978)*k + 1.781477937)*k - 0.356563782)*k + 0.319381530) * k;
  const cdf = 1 - stdNormPDF(Math.abs(x)) * p;
  return x >= 0 ? cdf : 1 - cdf;
}

function invNorm(p) {
  const q = Math.max(0.0001, Math.min(0.9999, p));
  const a = q - 0.5;
  if (Math.abs(a) < 0.42) {
    const r = a * a;
    return a * (2.5066 + r * (-18.615 + r * (41.391 + r * -25.441))) /
           (1 + r * (-8.474 + r * (23.083 + r * (-21.062 + r * 3.131))));
  }
  const r = Math.sqrt(-2 * Math.log(q < 0.5 ? q : 1 - q));
  const s = q < 0.5 ? -1 : 1;
  return s * (r - (2.515 + 0.803*r + 0.010*r*r) / (1 + 1.433*r + 0.189*r*r + 0.001*r*r*r));
}

// --- Segment value simulation ---

function gatherSegmentValues(segments, min, max) {
  const vals = [];
  for (const seg of segments) {
    if (!seg) continue;
    const sMin = seg.min ?? min;
    const sMax = seg.max ?? max;
    const kw   = seg.kwargs ?? {};
    switch (seg.dist ?? 'step') {
      case 'step': {
        const step = kw.step ?? 10;
        for (let v = sMin; v <= sMax + step * 0.001; v += step) vals.push(v);
        break;
      }
      case 'uniform': {
        const res = Math.max(kw.resolution ?? 10, 2);
        for (let i = 0; i < res; i++) vals.push(sMin + (sMax - sMin) * i / (res - 1));
        break;
      }
      case 'power': {
        const res = Math.max(kw.resolution ?? 10, 2);
        const b   = kw.bias ?? 1.5;
        for (let i = 0; i < res; i++) vals.push(sMin + (sMax - sMin) * Math.pow(i / (res - 1), b));
        break;
      }
      case 'geometric': {
        const res = Math.max(kw.resolution ?? 10, 2);
        const sm  = Math.max(sMin, 1e-9);
        for (let i = 0; i < res; i++) vals.push(sm * Math.pow(Math.max(sMax, sm + 1e-9) / sm, i / (res - 1)));
        break;
      }
    }
  }
  return vals;
}

// --- Bar heights ---

function computeHeights(dist, bars, { bias, segments, min, max, midpoint, skew, std }) {
  const range = max - min || 1;

  if (dist === 'uniform' || dist === 'step') {
    return Array(bars).fill(65);
  }

  if (dist === 'gaussian') {
    const mu    = midpoint != null ? midpoint : (min + max) / 2;
    const sigma = std != null ? std : range / 6;
    const raw = Array.from({ length: bars }, (_, i) => {
      const x = min + range * (i + 0.5) / bars;
      const z = (x - mu) / sigma;
      return 2 * stdNormPDF(z) * stdNormCDF(skew * z);
    });
    const peak = Math.max(...raw, 1e-10);
    return raw.map(v => Math.max((v / peak) * 100, 2));
  }

  if (dist === 'power') {
    const N    = bars * 40;
    const bkts = new Array(bars).fill(0);
    for (let k = 0; k <= N; k++) {
      const y = Math.pow(k / N, bias);
      bkts[Math.min(Math.floor(y * bars), bars - 1)]++;
    }
    const mx = Math.max(...bkts, 1);
    return bkts.map(b => Math.max(b / mx * 100, 4));
  }

  if (dist === 'geometric') {
    const N    = bars * 40;
    const bkts = new Array(bars).fill(0);
    for (let k = 0; k <= N; k++) {
      const y = Math.log1p((k / N) * (Math.E - 1));
      bkts[Math.min(Math.floor(y * bars), bars - 1)]++;
    }
    const mx = Math.max(...bkts, 1);
    return bkts.map(b => Math.max(b / mx * 100, 4));
  }

  if (dist === 'segmented' && segments.length > 0) {
    const vals = gatherSegmentValues(segments, min, max);
    const bkts = new Array(bars).fill(0);
    for (const v of vals) {
      if (v < min || v > max) continue;
      bkts[Math.min(Math.floor((v - min) / range * bars), bars - 1)]++;
    }
    const mx = Math.max(...bkts, 1);
    return bkts.map(b => b > 0 ? Math.max(b / mx * 100, 4) : 2);
  }

  return Array(bars).fill(65);
}

// --- Tick positions ---

function computeTicks(dist, n, { bias, segments, min, max, midpoint, skew, std }) {
  const range = max - min || 1;

  if (dist === 'segmented' && segments.length > 0) {
    const vals = gatherSegmentValues(segments, min, max);
    return vals.map(v => (v - min) / range).filter(p => p >= 0 && p <= 1);
  }

  if (dist === 'uniform' || dist === 'step') {
    if (n <= 1) return [0];
    return Array.from({ length: n }, (_, i) => i / (n - 1));
  }

  if (dist === 'power') {
    if (n <= 1) return [0];
    return Array.from({ length: n }, (_, i) => Math.pow(i / (n - 1), bias));
  }

  if (dist === 'geometric') {
    if (n <= 1) return [0];
    return Array.from({ length: n }, (_, i) => {
      const t = i / (n - 1);
      return Math.log1p(t * (Math.E - 1));
    });
  }

  if (dist === 'gaussian') {
    const mu    = midpoint != null ? midpoint : (min + max) / 2;
    const sigma = std != null ? std : range / 6;
    return Array.from({ length: n }, (_, i) => {
      const p = (i + 0.5) / n;
      const val = mu + sigma * invNorm(p);
      return Math.max(0, Math.min(1, (val - min) / range));
    });
  }

  return [];
}

// --- Component ---

export function DistHistogram({
  dist,
  distKwargs = {},
  color = '#5b35d5',
  bars   = 10,
  min    = 0,
  max    = 100,
}) {
  const {
    bias     = 1.5,
    segments = [],
    midpoint = null,
    skew     = 0,
    std      = null,
  } = distKwargs;

  const opts    = { bias, segments, min, max, midpoint, skew, std };
  const heights = computeHeights(dist, bars, opts);
  const ticks   = computeTicks(dist, bars, opts);

  const MAX_TICKS = 80;
  const displayTicks = ticks.length > MAX_TICKS
    ? ticks.filter((_, i) => i % Math.ceil(ticks.length / MAX_TICKS) === 0)
    : ticks;

  const range = max - min || 1;
  const midLinePct = dist === 'gaussian'
    ? ((midpoint != null ? midpoint : (min + max) / 2) - min) / range * 100
    : null;

  function isHighlighted(i) {
    if (dist === 'power') return bias >= 1 ? i === 0 : i === bars - 1;
    if (dist === 'gaussian') {
      const mu = midpoint != null ? midpoint : (min + max) / 2;
      return i === Math.min(Math.floor((mu - min) / range * bars), bars - 1);
    }
    return false;
  }

  function segColor(i) {
    if (dist !== 'segmented' || segments.length === 0) return null;
    const barCenter = min + range * (i + 0.5) / bars;
    for (let s = 0; s < segments.length; s++) {
      const sMin = segments[s]?.min ?? min;
      const sMax = segments[s]?.max ?? max;
      if (barCenter >= sMin && barCenter <= sMax) {
        return s % 2 === 0 ? color : `${color}88`;
      }
    }
    return `${color}15`;
  }

  const segBoundaries = (dist === 'segmented' && segments.length > 1)
    ? segments.slice(0, -1).map(seg => {
        const segMax = seg?.max ?? max;
        return ((segMax - min) / range) * 100;
      }).filter(p => p > 0 && p < 100)
    : [];

  return (
    <div>
      <div className="dist-histogram__bars">
        {midLinePct != null && (
          <div
            className="dist-histogram__guide-line"
            style={{ left: `${midLinePct}%`, borderLeft: `1px dashed ${color}66` }}
          />
        )}
        {segBoundaries.map((pct, i) => (
          <div
            key={`sb-${i}`}
            className="dist-histogram__seg-boundary"
            style={{ left: `${pct}%` }}
          />
        ))}
        {heights.map((h, i) => (
          <div
            key={i}
            className="dist-histogram__bar"
            style={{
              height: `${Math.max(h, 3)}%`,
              backgroundColor: segColor(i) ?? (isHighlighted(i) ? color : `${color}55`),
            }}
          />
        ))}
      </div>

      <div className="dist-histogram__ticks">
        {displayTicks.map((pos, i) => (
          <div
            key={i}
            className="dist-histogram__tick"
            style={{ left: `${pos * 100}%`, backgroundColor: `${color}99` }}
          />
        ))}
      </div>
    </div>
  );
}
