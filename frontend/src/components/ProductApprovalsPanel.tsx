import React, { useCallback, useEffect, useState } from "react";
import { Check, X, Loader2, RefreshCw } from "lucide-react";
import { clientGet, clientPost } from "../lib/api";

interface Approval {
  id: string;
  product_name: string;
  nombre_estudiante: string;
  status: string;
  source: string;
  unit_price: number;
  created_at: string;
  expires_at?: string;
}

export const ProductApprovalsPanel: React.FC<{ apiBase: string; nitColegio?: string }> = ({
  apiBase,
  nitColegio,
}) => {
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const q = nitColegio ? `?nit_colegio=${encodeURIComponent(nitColegio)}` : "";
      const data = await clientGet<Approval[]>(apiBase, `/approvals/pending${q}`);
      setItems(data || []);
    } finally {
      setLoading(false);
    }
  }, [apiBase, nitColegio]);

  useEffect(() => {
    load();
  }, [load]);

  const resolve = async (id: string, decision: "allow" | "block") => {
    setBusyId(id);
    try {
      await clientPost(apiBase, `/approvals/${id}/resolve`, { decision });
      setItems((list) => list.filter((i) => i.id !== id));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <p className="text-sm text-bio-500 py-8 text-center" data-testid="approvals-loading">
        <Loader2 className="h-5 w-5 animate-spin inline mr-2" />
        Cargando cola de aprobación…
      </p>
    );
  }

  if (items.length === 0) {
    return (
      <p className="text-sm text-bio-500 py-8 text-center rounded-xl border border-dashed border-bio-200" data-testid="approvals-empty">
        No hay productos pendientes de aprobación parental.
      </p>
    );
  }

  return (
    <div data-testid="product-approvals-panel">
      <div className="flex justify-end mb-3">
        <button
          type="button"
          onClick={load}
          className="text-xs text-brand inline-flex items-center gap-1"
          data-testid="approvals-refresh"
        >
          <RefreshCw className="h-3.5 w-3.5" /> Actualizar
        </button>
      </div>
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.id} className="rounded-xl border border-bio-200 bg-white p-4" data-testid={`approval-${item.id}`}>
            <p className="text-[10px] font-mono uppercase text-brand">{item.source === "catalog_new" ? "Catálogo nuevo" : "Plan semanal"}</p>
            <p className="font-medium text-bio-900 mt-1">{item.product_name}</p>
            <p className="text-xs text-bio-500 mt-1">
              {item.nombre_estudiante} · ${item.unit_price?.toLocaleString("es-CO")}
            </p>
            <div className="flex gap-2 mt-3">
              <button
                type="button"
                disabled={busyId === item.id}
                onClick={() => resolve(item.id, "allow")}
                data-testid={`approve-${item.id}`}
                className="inline-flex items-center gap-1 rounded-lg bg-ok/10 text-ok border border-ok/30 px-3 py-1.5 text-sm font-medium disabled:opacity-50"
              >
                <Check className="h-4 w-4" /> Permitir
              </button>
              <button
                type="button"
                disabled={busyId === item.id}
                onClick={() => resolve(item.id, "block")}
                data-testid={`block-${item.id}`}
                className="inline-flex items-center gap-1 rounded-lg bg-red-50 text-danger border border-red-200 px-3 py-1.5 text-sm font-medium disabled:opacity-50"
              >
                <X className="h-4 w-4" /> Bloquear
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ProductApprovalsPanel;
