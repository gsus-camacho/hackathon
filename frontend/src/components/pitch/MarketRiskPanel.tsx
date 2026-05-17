import React from "react";
import { AlertTriangle } from "lucide-react";

const competitorRows = [
  { label: "Usuarios", katu: "140.000", biofood: "—", pct: 100 },
  { label: "Países", katu: "8", biofood: "—", pct: 80 },
  { label: "Canal padre", katu: "Sí", biofood: "Parcial", pct: 92 },
];

export const MarketRiskPanel: React.FC = () => (
  <section className="grid grid-cols-1 lg:grid-cols-3 gap-4" data-testid="market-risk-panel">
    <article className="rounded-xl border border-red-200 bg-red-50/50 p-6 flex flex-col justify-between">
      <div>
        <span className="text-[10px] font-mono uppercase tracking-wide text-danger">Indicador interno</span>
        <p className="font-heading text-6xl font-semibold text-danger mt-3" data-testid="risk-unlinked-pct">
          60%
        </p>
        <p className="text-sm text-danger/90 mt-3 max-w-xs">
          de los registros de recargas no tienen un padre vinculado al estudiante.
        </p>
      </div>
      <span className="inline-flex items-center gap-2 mt-6 text-xs font-medium text-danger bg-white border border-red-200 rounded-full px-3 py-1 w-fit">
        <span className="w-1.5 h-1.5 rounded-full bg-danger" />
        Comunicación rota
      </span>
    </article>

    <article className="rounded-xl border border-bio-200 bg-white p-6 lg:col-span-1">
      <span className="text-[10px] font-mono uppercase tracking-wide text-bio-500">Posicionamiento comparado</span>
      <p className="text-xs text-bio-500 mt-1 mb-4">Competidor de referencia: Katú</p>
      <ul className="space-y-3" data-testid="competitor-benchmark">
        {competitorRows.map((r) => (
          <li key={r.label}>
            <div className="flex justify-between text-xs font-mono text-bio-500 mb-1">
              <span>{r.label}</span>
              <span className="text-bio-700">{r.katu}</span>
            </div>
            <div className="h-2 bg-bio-100 rounded-full overflow-hidden">
              <div className="h-full bg-brand rounded-full" style={{ width: `${r.pct}%` }} />
            </div>
            <div className="flex justify-between text-[10px] text-bio-500 mt-1">
              <span>Biofood hoy</span>
              <span>{r.biofood}</span>
            </div>
          </li>
        ))}
      </ul>
    </article>

    <article className="rounded-xl border border-bio-200 bg-white p-6 flex flex-col justify-between">
      <div>
        <span className="text-[10px] font-mono uppercase tracking-wide text-bio-500">Consecuencia operativa</span>
        <p className="font-medium text-bio-900 mt-4 text-lg leading-snug">Sin canal directo, no hay retención.</p>
        <p className="text-sm text-bio-500 mt-3">
          Las plataformas con interacción bidireccional capturan al usuario que nosotros solo registramos.
        </p>
      </div>
      <span className="inline-flex items-center gap-2 mt-6 text-xs font-medium text-warn bg-amber-50 border border-amber-200 rounded-full px-3 py-1 w-fit">
        <AlertTriangle className="h-3.5 w-3.5" />
        Ventana de oportunidad
      </span>
    </article>
  </section>
);

export default MarketRiskPanel;
