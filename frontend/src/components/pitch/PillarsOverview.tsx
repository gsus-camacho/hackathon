import React from "react";
import { Package, ShieldAlert, TrendingUp, ArrowRight } from "lucide-react";

const pillars = [
  {
    id: "01",
    key: "discounts",
    href: "/discounts",
    icon: Package,
    title: "Flujo de caja anticipado",
    desc: "Paquetes con incentivo, micro-rating WhatsApp y control parental por producto nuevo.",
    testId: "pillar-card-01",
  },
  {
    id: "02",
    key: "allergens",
    href: "/allergens",
    icon: ShieldAlert,
    title: "Seguridad nutricional",
    desc: "Preferencias alimentarias unificadas + bloqueo automático con Gemini.",
    testId: "pillar-card-02",
  },
  {
    id: "03",
    key: "benchmark",
    href: "/benchmark",
    icon: TrendingUp,
    title: "Inteligencia B2B",
    desc: "Benchmark nacional × Satisfaction Index para decisiones de inventario.",
    testId: "pillar-card-03",
  },
];

export const PillarsOverview: React.FC = () => (
  <section className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="pillars-overview">
    {pillars.map((p) => {
      const Icon = p.icon;
      return (
        <a
          key={p.key}
          href={p.href}
          data-testid={p.testId}
          className="group rounded-xl border border-bio-200 bg-white p-5 hover:-translate-y-0.5 hover:shadow-card transition-all duration-200"
        >
          <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-bio-500">Pilar {p.id}</span>
          <div className="flex items-center gap-2 mt-2 mb-2">
            <span className="rounded-lg bg-brand-soft text-brand p-2">
              <Icon className="h-4 w-4" />
            </span>
            <h3 className="font-heading font-semibold text-bio-900">{p.title}</h3>
          </div>
          <p className="text-sm text-bio-500 leading-relaxed">{p.desc}</p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-brand mt-4 group-hover:gap-2 transition-all">
            Explorar <ArrowRight className="h-3.5 w-3.5" />
          </span>
        </a>
      );
    })}
  </section>
);

export default PillarsOverview;
