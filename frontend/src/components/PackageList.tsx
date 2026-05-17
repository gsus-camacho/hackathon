import React, { useState } from "react";
import { Loader2, Sparkles, Trash2 } from "lucide-react";
import { clientDelete, clientPost } from "../lib/api";

interface PackageItem { product_name: string; quantity: number; unit_price: number; }
interface Pkg {
  id: string;
  name: string;
  description: string;
  items: PackageItem[];
  original_total: number;
  discounted_total: number;
  discount_pct: number;
  target_segment: string;
  valid_until?: string;
  active: boolean;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n);

const segmentLabel: Record<string, string> = {
  general: "General",
  low_balance: "Saldo bajo",
  high_consumption: "Alto consumo",
  no_consumption: "Sin consumo",
};

export const PackageList: React.FC<{ apiBase: string; initial: Pkg[] }> = ({ apiBase, initial }) => {
  const [pkgs, setPkgs] = useState<Pkg[]>(initial || []);
  const [busy, setBusy] = useState(false);

  const generate = async () => {
    setBusy(true);
    try {
      const data: Pkg[] = await clientPost(apiBase, "/discounts/packages/generate");
      setPkgs((c) => [...data, ...c]);
    } finally {
      setBusy(false);
    }
  };

  const deactivate = async (id: string) => {
    await clientDelete(apiBase, `/discounts/packages/${id}`);
    setPkgs((c) => c.filter((p) => p.id !== id));
  };

  return (
    <div data-testid="package-list">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="font-heading text-2xl font-semibold tracking-tight text-bio-900">Paquetes dinámicos</h2>
          <p className="text-sm text-bio-500 mt-1">
            Generados automáticamente a partir de los productos más vendidos en Biofood.
          </p>
        </div>
        <button
          onClick={generate}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="generate-packages-btn"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Generar paquetes
        </button>
      </div>
      {pkgs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
          <p className="text-bio-500">No hay paquetes activos. Pulsa <strong>Generar paquetes</strong>.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pkgs.map((p) => (
            <div
              key={p.id}
              className="rounded-xl border border-bio-200 bg-white p-5 transition-all hover:-translate-y-0.5 hover:shadow-card animate-fade-up"
              data-testid={`package-card-${p.id}`}
            >
              <div className="flex items-start justify-between">
                <span className="text-[10px] uppercase tracking-[0.18em] font-mono text-bio-500">
                  {segmentLabel[p.target_segment] || p.target_segment}
                </span>
                <button
                  onClick={() => deactivate(p.id)}
                  className="text-bio-500 hover:text-danger transition-colors"
                  data-testid={`deactivate-${p.id}`}
                  aria-label="Desactivar"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              <h3 className="font-heading font-semibold text-bio-900 mt-1">{p.name}</h3>
              <p className="text-xs text-bio-500 mt-1 mb-4 line-clamp-2">{p.description}</p>
              <ul className="space-y-1 text-sm">
                {p.items.map((i, idx) => (
                  <li key={idx} className="flex items-center justify-between text-bio-700">
                    <span className="truncate pr-2">{i.product_name}</span>
                    <span className="font-mono text-xs text-bio-500">x{i.quantity}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 pt-4 border-t border-bio-200 flex items-end justify-between">
                <div>
                  <div className="text-xs text-bio-500 line-through font-mono">{fmt(p.original_total)}</div>
                  <div className="font-heading text-xl font-semibold text-bio-900">
                    {fmt(p.discounted_total)}
                  </div>
                </div>
                <span className="text-xs font-mono px-2 py-1 rounded-md bg-emerald-50 text-ok">
                  -{p.discount_pct}%
                </span>
              </div>
              {p.valid_until && (
                <div className="mt-3 text-[10px] font-mono text-bio-500">Válido hasta {p.valid_until}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PackageList;
