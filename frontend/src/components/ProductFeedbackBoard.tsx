import React, { useEffect, useState } from "react";
import { ThumbsUp, ThumbsDown, Loader2 } from "lucide-react";
import { clientGet, clientPost } from "../lib/api";

interface Product { name: string; units: number; revenue: number; }
interface Feedback { product_name: string; up: number; down: number; total: number; score_pct: number; }

export const ProductFeedbackBoard: React.FC<{ apiBase: string; products: Product[] }> = ({ apiBase, products }) => {
  const [feedback, setFeedback] = useState<Record<string, Feedback>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = async () => {
    const data: Feedback[] = await clientGet(apiBase, "/feedback/products");
    const map: Record<string, Feedback> = {};
    for (const f of data) map[f.product_name] = f;
    setFeedback(map);
  };

  useEffect(() => { refresh(); }, [apiBase]);

  const vote = async (product: string, kind: "up" | "down") => {
    setBusy(product + kind);
    try {
      await clientPost(apiBase, "/feedback/vote", { product_name: product, vote: kind });
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  if (!products.length) {
    return (
      <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
        <p className="text-sm text-bio-500">No hay productos disponibles para votar.</p>
      </div>
    );
  }

  return (
    <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="product-feedback-grid">
      {products.map((p) => {
        const f = feedback[p.name];
        const up = f?.up || 0;
        const down = f?.down || 0;
        const total = up + down;
        const score = total ? (up / total) * 100 : 50;
        return (
          <li
            key={p.name}
            className="group relative rounded-xl border border-bio-200 bg-white overflow-hidden hover:-translate-y-0.5 hover:shadow-card transition-all duration-200 animate-fade-up"
            data-testid={`product-card-${p.name}`}
          >
            <div className="flex">
              <button
                onClick={() => vote(p.name, "up")}
                disabled={busy !== null}
                className="flex flex-col items-center justify-center gap-1 px-4 py-6 bg-emerald-50 hover:bg-emerald-100 text-ok transition-colors disabled:opacity-50"
                data-testid={`vote-up-${p.name}`}
                aria-label="Me gusta"
              >
                {busy === p.name + "up" ? <Loader2 className="h-5 w-5 animate-spin" /> : <ThumbsUp className="h-5 w-5" />}
                <span className="text-xs font-mono font-semibold">{up}</span>
              </button>
              <div className="flex-1 p-5 min-w-0">
                <h3 className="font-heading font-semibold text-bio-900 truncate" data-testid={`product-name-${p.name}`}>{p.name}</h3>
                <div className="mt-1 text-xs font-mono text-bio-500">{p.units} unidades vendidas</div>
                {total > 0 && (
                  <>
                    <div className="mt-3 h-1.5 rounded-full bg-bio-100 overflow-hidden">
                      <div
                        className={`h-full ${score >= 50 ? "bg-ok" : "bg-danger"}`}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                    <div className="mt-1 text-[10px] font-mono text-bio-500" data-testid={`product-score-${p.name}`}>
                      {score.toFixed(0)}% positivo · {total} votos
                    </div>
                  </>
                )}
              </div>
              <button
                onClick={() => vote(p.name, "down")}
                disabled={busy !== null}
                className="flex flex-col items-center justify-center gap-1 px-4 py-6 bg-red-50 hover:bg-red-100 text-danger transition-colors disabled:opacity-50"
                data-testid={`vote-down-${p.name}`}
                aria-label="No me gusta"
              >
                {busy === p.name + "down" ? <Loader2 className="h-5 w-5 animate-spin" /> : <ThumbsDown className="h-5 w-5" />}
                <span className="text-xs font-mono font-semibold">{down}</span>
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export default ProductFeedbackBoard;
