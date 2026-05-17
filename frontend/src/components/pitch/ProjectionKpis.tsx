import React from "react";

export const ProjectionKpis: React.FC = () => (
  <section className="grid grid-cols-1 lg:grid-cols-3 gap-4" data-testid="projection-kpis">
    <article className="rounded-xl border border-bio-200 bg-white p-6">
      <span className="text-[10px] font-mono uppercase tracking-wide text-brand">Pilar 01 · Flujo de caja</span>
      <p className="text-xs text-bio-500 mt-1">Ticket promedio</p>
      <p className="font-heading text-5xl sm:text-6xl font-semibold text-brand mt-2" data-testid="kpi-ticket-target">
        +20%
      </p>
      <p className="text-xs text-bio-500">objetivo mínimo</p>
      <p className="text-sm text-bio-500 mt-6 pt-4 border-t border-bio-100 leading-relaxed">
        Consolidación de recargas reactivas en paquetes mensuales con incentivo. Liquidez anticipada para la cafetería.
      </p>
    </article>
    <article className="rounded-xl border border-bio-200 bg-white p-6">
      <span className="text-[10px] font-mono uppercase tracking-wide text-ok">Pilar 01 · Retención</span>
      <p className="text-xs text-bio-500 mt-1">Saldos en cero</p>
      <p className="font-heading text-5xl sm:text-6xl font-semibold text-ok mt-2" data-testid="kpi-zero-balance-target">
        −30%
      </p>
      <p className="text-xs text-bio-500">objetivo mínimo</p>
      <p className="text-sm text-bio-500 mt-6 pt-4 border-t border-bio-100 leading-relaxed">
        Alertas preventivas vía WhatsApp y recarga conversacional eliminan la latencia entre intención y acción.
      </p>
    </article>
    <article className="rounded-xl bg-bio-900 text-white p-6 grain">
      <span className="text-[10px] font-mono uppercase tracking-wide text-bio-500">Pilar 03 · B2B</span>
      <p className="text-xs text-bio-200 mt-1">Conversión cafetería</p>
      <p className="font-heading text-2xl font-semibold text-white mt-3 leading-tight">
        Inventario informado por SI + Benchmark.
      </p>
      <p className="text-sm text-bio-200 mt-6 pt-4 border-t border-bio-800 leading-relaxed">
        10 años de datos transaccionales propietarios. Barrera de entrada que ningún competidor reciente puede replicar.
      </p>
    </article>
  </section>
);

export default ProjectionKpis;
