import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
  } from "recharts";
  
  export default function PriceChart({ prices }) {
    const data = prices.map((p, i) => ({
      index: i,
      price: p,
    }));
  
    return (
      <LineChart width={800} height={400} data={data}>
        <XAxis dataKey="index" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="price" />
      </LineChart>
    );
  }
  