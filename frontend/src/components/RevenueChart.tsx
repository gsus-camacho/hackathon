import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface DailyPoint {
  date: string;
  ventas: number;
  recargas: number;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("es-CO", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const RevenueChart: React.FC<{ data: DailyPoint[] }> = ({ data }) => {
  return (
    <div className="h-72 w-full" data-testid="revenue-chart">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="ventasFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2563EB" stopOpacity={0.32} />
              <stop offset="100%" stopColor="#2563EB" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="recargasFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#10B981" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#E2E8F0" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#64748B" }}
            tickFormatter={(v) => v.slice(5)}
            stroke="#CBD5E1"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#64748B" }}
            stroke="#CBD5E1"
            tickFormatter={(v) => fmt(Number(v))}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #E2E8F0",
              fontSize: 12,
              fontFamily: "IBM Plex Sans",
            }}
            formatter={(v: any) => fmt(Number(v))}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area
            type="monotone"
            dataKey="ventas"
            stroke="#2563EB"
            strokeWidth={2}
            fill="url(#ventasFill)"
            name="Ventas"
          />
          <Area
            type="monotone"
            dataKey="recargas"
            stroke="#10B981"
            strokeWidth={2}
            fill="url(#recargasFill)"
            name="Recargas"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RevenueChart;
