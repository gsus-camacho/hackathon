import React from "react";

interface Product {
  name: string;
  units: number;
  revenue: number;
}

const fmtCop = (n: number) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(n);

export const TopProducts: React.FC<{ products: Product[] }> = ({ products }) => {
  const max = Math.max(...products.map((p) => p.revenue), 1);
  return (
    <ul className="space-y-3" data-testid="top-products-list">
      {products.map((p, i) => (
        <li key={p.name} data-testid={`product-row-${i}`}>
          <div className="flex items-center justify-between text-sm">
            <span className="text-bio-900 font-medium truncate pr-3">{p.name}</span>
            <span className="font-mono text-bio-500 text-xs whitespace-nowrap">
              {p.units} u · {fmtCop(p.revenue)}
            </span>
          </div>
          <div className="mt-1.5 h-1.5 rounded-full bg-bio-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-brand transition-all"
              style={{ width: `${(p.revenue / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
      {products.length === 0 && (
        <li className="text-sm text-bio-500">Sin datos.</li>
      )}
    </ul>
  );
};

export default TopProducts;
