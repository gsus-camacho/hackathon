import React from "react";

interface BenchmarkItem {
  product: string;
  delta: number;
}

export const BenchmarkChart: React.FC<{ data: BenchmarkItem[] }> = ({ data }) => {
  const maxAbs = Math.max(...data.map((d) => Math.abs(d.delta)), 1);

  return (
    <div className="space-y-3" data-testid="benchmark-chart">
      {data.map((item, i) => {
        const pct = Math.abs(item.delta) / maxAbs * 100;
        const isPositive = item.delta >= 0;
        return (
          <div key={i} className="flex items-center gap-3" data-testid={`bench-row-${i}`}>
            <span className="w-40 text-sm text-slate-700 truncate font-medium">{item.product}</span>
            <div className="flex-1 h-5 bg-slate-100 rounded overflow-hidden relative">
              <div
                className={`h-full rounded transition-all duration-700 ${isPositive ? "bg-blue-500" : "bg-slate-400"}`}
                style={{ width: `${Math.max(pct, 4)}%` }}
              />
            </div>
            <span className={`w-16 text-right text-sm font-mono font-medium ${isPositive ? "text-blue-600" : "text-slate-500"}`}>
              {isPositive ? "+" : ""}{item.delta}%
            </span>
          </div>
        );
      })}
      <p className="text-xs text-slate-400 font-mono mt-2">Eje · ventas mes vs. mediana nacional del segmento</p>
    </div>
  );
};

export default BenchmarkChart;
