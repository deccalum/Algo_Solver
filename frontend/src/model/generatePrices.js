export function generatePrices(model) {
  const { minPrice, maxPrice, inflation, zones } = model;
  
  const totalSpanShare = zones.reduce((sum, z) => sum + z.spanShare, 0);
    const totalSpan = (maxPrice - minPrice) * inflation;
  
    let current = minPrice;
    let prices = [];
  
    zones.forEach((zone) => {
      const normalizedSpanShare = zone.spanShare / totalSpanShare;
      const span = totalSpan * normalizedSpanShare;
  
      const start = current;
      const end = start + span;
  
      let zonePrices = [];
  
      if (zone.mode === "exact") {
        const count = Math.max(Math.floor(span / zone.step), 1);
        for (let i = 0; i <= count; i++) {
          zonePrices.push(start + (span * i) / count);
        }
      } else {
        for (let i = 0; i < zone.resolution; i++) {
          const t = i / (zone.resolution - 1);
          let shaped = t;
  
          if (zone.mode === "power") shaped = Math.pow(t, zone.bias);
          if (zone.mode === "s-curve")
            shaped = 3 * t * t - 2 * t * t * t;
          if (zone.mode === "exponential")
            shaped =
              (Math.exp(zone.bias * t) - 1) /
              (Math.exp(zone.bias) - 1);
  
          zonePrices.push(start + span * shaped);
        }
      }
  
      prices = prices.concat(zonePrices);
      current = end;
    });
  
    return prices;
  }
  