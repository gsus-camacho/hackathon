import React from "react";
import { Clock, Calendar, ShieldAlert, Wallet, FileBarChart } from "lucide-react";

const triggers = [
  {
    id: "balance",
    icon: Wallet,
    title: "Saldo bajo preventivo",
    desc: "Alerta WhatsApp antes de que el saldo llegue a cero. Recarga en el mismo hilo.",
    schedule: "Continuo · umbral configurable",
    pillar: "01",
    color: "text-warn bg-amber-50",
  },
  {
    id: "consumption",
    icon: Clock,
    title: "Sin consumo @ 12:00 PM",
    desc: "Si el estudiante no ha consumido al mediodía, notifica al acudiente.",
    schedule: "Diario · 12:00 PM",
    pillar: "01",
    color: "text-brand bg-brand-soft",
  },
  {
    id: "allergen",
    icon: ShieldAlert,
    title: "Producto incompatible",
    desc: "Bloqueo en POS + alerta al padre cuando se detecta riesgo alimentario.",
    schedule: "En tiempo real",
    pillar: "02",
    color: "text-danger bg-red-50",
  },
  {
    id: "rating",
    icon: FileBarChart,
    title: "Micro-rating post-consumo",
    desc: "Tras cada compra, solicita 👍/👎 para alimentar el Satisfaction Index.",
    schedule: "Post-transacción",
    pillar: "01 → 03",
    color: "text-ok bg-emerald-50",
  },
  {
    id: "friday",
    icon: Calendar,
    title: "Reporte nutricional viernes",
    desc: "Resumen semanal de consumo y balance enviado por WhatsApp.",
    schedule: "Viernes · 4:00 PM",
    pillar: "01",
    color: "text-bio-700 bg-bio-100",
  },
];

export const NotificationTriggersPanel: React.FC = () => (
  <ul className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="notification-triggers">
    {triggers.map((t) => {
      const Icon = t.icon;
      return (
        <li key={t.id} className="rounded-xl border border-bio-200 bg-white p-4 flex gap-3" data-testid={`trigger-${t.id}`}>
          <span className={`rounded-lg p-2 h-fit shrink-0 ${t.color}`}>
            <Icon className="h-4 w-4" />
          </span>
          <span className="min-w-0">
            <span className="text-[10px] font-mono text-bio-500">Pilar {t.pillar}</span>
            <p className="font-medium text-bio-900">{t.title}</p>
            <p className="text-sm text-bio-500 mt-1">{t.desc}</p>
            <p className="text-[11px] font-mono text-bio-500 mt-2">{t.schedule}</p>
          </span>
        </li>
      );
    })}
  </ul>
);

export default NotificationTriggersPanel;
