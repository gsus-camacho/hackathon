import React, { useState } from "react";
import { Star, Send } from "lucide-react";

interface Rating {
  id: string;
  score: number;
  comment?: string;
  product_name?: string;
  nit_colegio?: string;
  source?: string;
  created_at?: string;
}

export const FeedbackPanel: React.FC<{ apiBase: string; initial: Rating[]; summary: { average: number; count: number } }> = ({ apiBase, initial, summary }) => {
  const [list, setList] = useState<Rating[]>(initial || []);
  const [stats, setStats] = useState(summary);
  const [score, setScore] = useState(5);
  const [comment, setComment] = useState("");
  const [product, setProduct] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch(`${apiBase}/api/feedback/ratings`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ score, comment, product_name: product || undefined, source: "dashboard" }),
      });
      const data: Rating = await res.json();
      setList((c) => [data, ...c]);
      const sumRes = await fetch(`${apiBase}/api/feedback/summary`);
      setStats(await sumRes.json());
      setComment("");
      setProduct("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-5 gap-6" data-testid="feedback-panel">
      <div className="lg:col-span-2 space-y-4">
        <div className="rounded-xl border border-bio-200 bg-white p-5">
          <div className="text-xs uppercase tracking-[0.18em] text-bio-500 font-mono">Satisfacción</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-heading text-4xl font-semibold text-bio-900">{stats.average.toFixed(2)}</span>
            <span className="text-sm text-bio-500">/ 5</span>
          </div>
          <div className="flex items-center gap-0.5 mt-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star
                key={i}
                className={`h-4 w-4 ${i <= Math.round(stats.average) ? "text-amber-400 fill-amber-400" : "text-bio-200"}`}
              />
            ))}
            <span className="ml-2 text-xs text-bio-500 font-mono">{stats.count} ratings</span>
          </div>
        </div>
        <form onSubmit={submit} className="rounded-xl border border-bio-200 bg-white p-5 space-y-3">
          <h3 className="font-heading font-semibold text-bio-900">Nuevo rating</h3>
          <div>
            <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Puntaje</label>
            <div className="flex items-center gap-1 mt-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <button
                  type="button"
                  key={i}
                  onClick={() => setScore(i)}
                  className={`h-9 w-9 grid place-items-center rounded-lg transition-colors ${
                    i <= score ? "text-amber-400 bg-amber-50" : "text-bio-500 hover:bg-bio-100"
                  }`}
                  data-testid={`star-${i}`}
                  aria-label={`${i} estrellas`}
                >
                  <Star className={`h-5 w-5 ${i <= score ? "fill-amber-400" : ""}`} />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Producto (opcional)</label>
            <input
              value={product}
              onChange={(e) => setProduct(e.target.value)}
              className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
              data-testid="rating-product"
            />
          </div>
          <div>
            <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Comentario</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
              data-testid="rating-comment"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
            data-testid="rating-submit-btn"
          >
            <Send className="h-4 w-4" /> Enviar rating
          </button>
        </form>
      </div>
      <div className="lg:col-span-3">
        <h3 className="font-heading font-semibold text-bio-900 mb-3">Últimos comentarios</h3>
        {list.length === 0 ? (
          <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
            <p className="text-sm text-bio-500">No hay ratings aún. Envía el primero.</p>
          </div>
        ) : (
          <ul className="space-y-3" data-testid="rating-list">
            {list.map((r) => (
              <li
                key={r.id}
                className="rounded-xl border border-bio-200 bg-white p-4"
                data-testid={`rating-row-${r.id}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star
                        key={i}
                        className={`h-4 w-4 ${i <= r.score ? "text-amber-400 fill-amber-400" : "text-bio-200"}`}
                      />
                    ))}
                  </div>
                  <span className="text-[10px] font-mono text-bio-500">
                    {r.source} · {r.created_at?.slice(0, 10)}
                  </span>
                </div>
                {r.product_name && (
                  <div className="text-xs font-mono text-bio-500 mt-2">Producto: {r.product_name}</div>
                )}
                {r.comment && <p className="text-sm text-bio-700 mt-1">{r.comment}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default FeedbackPanel;
