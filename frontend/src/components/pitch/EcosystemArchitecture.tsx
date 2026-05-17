import React from "react";
import { Smartphone, LayoutDashboard, MessageCircle, Database } from "lucide-react";

const nodes = [
  {
    tag: "Interfaz · Padres",
    title: "App Móvil",
    desc: "Perfil del estudiante, preferencias alimentarias, recargas.",
    icon: Smartphone,
    href: "/hijos",
    testId: "arch-node-mobile",
  },
  {
    tag: "Core transaccional",
    title: "Biofood / Angular",
    desc: "7.2M registros · catálogo · biometría · POS cafetería.",
    icon: Database,
    primary: true,
    testId: "arch-node-core",
  },
  {
    tag: "Interfaz · Cafeterías",
    title: "Dashboard Analítico",
    desc: "Benchmark nacional + Satisfaction Index sobre datos propietarios.",
    icon: LayoutDashboard,
    href: "/benchmark",
    testId: "arch-node-dashboard",
  },
];

export const EcosystemArchitecture: React.FC = () => (
  <section data-testid="ecosystem-architecture">
    <p className="text-[10px] uppercase tracking-[0.22em] font-mono text-bio-500 mb-3">
      Arquitectura · extender, no reemplazar
    </p>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
      {nodes.map((n) => {
        const Icon = n.icon;
        const inner = (
          <article
            data-testid={n.testId}
            className={`rounded-xl border p-5 h-full ${
              n.primary
                ? "bg-bio-900 border-bio-800 text-white"
                : "bg-white border-bio-200 hover:shadow-card transition-shadow"
            }`}
          >
            <span
              className={`text-[10px] font-mono uppercase tracking-wide ${
                n.primary ? "text-bio-500" : "text-brand"
              }`}
            >
              {n.tag}
            </span>
            <div className="flex items-center gap-2 mt-2 mb-2">
              <Icon className={`h-5 w-5 ${n.primary ? "text-brand" : "text-bio-700"}`} />
              <h3 className={`font-heading font-semibold ${n.primary ? "text-white" : "text-bio-900"}`}>
                {n.title}
              </h3>
            </div>
            <p className={`text-sm ${n.primary ? "text-bio-200" : "text-bio-500"}`}>{n.desc}</p>
          </article>
        );
        return n.href ? (
          <a key={n.title} href={n.href} className="block">
            {inner}
          </a>
        ) : (
          <div key={n.title}>{inner}</div>
        );
      })}
    </div>
    <a
      href="/bot"
      data-testid="arch-node-whatsapp"
      className="block rounded-xl border border-dashed border-brand/40 bg-brand-soft/30 p-5 hover:bg-brand-soft/50 transition-colors"
    >
      <span className="text-[10px] font-mono uppercase tracking-wide text-brand">Canal asíncrono</span>
      <div className="flex items-center gap-2 mt-2">
        <MessageCircle className="h-5 w-5 text-brand" />
        <h3 className="font-heading font-semibold text-bio-900">Bot WhatsApp</h3>
      </div>
      <p className="text-sm text-bio-500 mt-1">Alertas, micro-ratings, recargas conversacionales y aprobación de productos.</p>
    </a>
  </section>
);

export default EcosystemArchitecture;
