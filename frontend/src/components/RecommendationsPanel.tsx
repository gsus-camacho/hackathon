import React, { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";

interface Rec {
  id: string;
  title: string;
  summary: string;
  rationale: string;
  kind: string;
  impact_score: number;
}

const kindBadge: Record<string, string> = {
  product: "bg-brand-soft text-brand",
  package: "bg-amber-50 text-warn",
  nutrition: "bg-emerald-50 text-ok",
  operational: "bg-bio-100 text-bio-700",
};

export const RecommendationsPanel: React.FC<{ apiBase: string; initial: Rec[] }> = ({
  apiBase,
  initial,
}) => {
  const [recs, setRecs] = useState<Rec[]>(initial || []);
  const [loading, setLoading] = useState(false);
  const [focus, setFocus] = useState<"general" | "revenue" | "nutrition" | "safety">("general");
  const [err, setErr] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setErr(null);
    try {
      const res = await fetch(`${apiBase}/api/recommendations/generate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ focus }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data: Rec[] = await res.json();
      setRecs((curr) => [...data, ...curr]);
    } catch (e: any) {
      setErr(e?.message || "Error generando recomendaciones");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="recommendations-panel">
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex items-center gap-1.5 rounded-lg border border-bio-200 bg-white p-1">
          {(["general", "revenue", "nutrition", "safety"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFocus(f)}
              className={`text-xs px-3 py-1.5 rounded-md transition-colors ${
                focus === f ? "bg-bio-900 text-white" : "text-bio-700 hover:bg-bio-100"
              }`}
              data-testid={`focus-${f}`}
            >
              {f === "general" ? "General" : f === "revenue" ? "Ingresos" : f === "nutrition" ? "Nutrición" : "Seguridad"}
            </button>
          ))}
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="generate-recs-btn"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          {loading ? "Generando…" : "Generar con Gemini"}
        </button>
      </div>
      {err && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 text-danger text-sm" data-testid="recs-error">
          {err}
        </div>
      )}
      {recs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center" data-testid="recs-empty">
          <Sparkles className="h-7 w-7 text-bio-500 mx-auto mb-3" />
          <div className="text-bio-900 font-medium">Ninguna recomendación todavía</div>
          <p className="text-sm text-bio-500 mt-1">
            Pulsa <strong>Generar con Gemini</strong> para crear insights basados en datos reales.
          </p>
        </div>
      ) : (
        <ul className="grid md:grid-cols-2 gap-4">
          {recs.map((r) => (
            <li
              key={r.id}
              className="rounded-xl border border-bio-200 bg-white p-5 hover:-translate-y-0.5 hover:shadow-card transition-all duration-200 animate-fade-up"
              data-testid={`rec-${r.id}`}
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <h3 className="font-heading font-semibold text-bio-900">{r.title}</h3>
                <span className={`text-[10px] uppercase tracking-wider font-mono px-2 py-0.5 rounded ${kindBadge[r.kind] || "bg-bio-100 text-bio-700"}`}>
                  {r.kind}
                </span>
              </div>
              <p className="text-sm text-bio-700 mb-3">{r.summary}</p>
              <p className="text-xs text-bio-500 mb-3 leading-relaxed">{r.rationale}</p>
              <div className="flex items-center justify-between text-xs">
                <span className="font-mono text-bio-500">Impacto</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 h-1.5 bg-bio-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-brand"
                      style={{ width: `${Math.min(100, r.impact_score)}%` }}
                    />
                  </div>
                  <span className="font-mono text-bio-900">{Math.round(r.impact_score)}</span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RecommendationsPanel;
