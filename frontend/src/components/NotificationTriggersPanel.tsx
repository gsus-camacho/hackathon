import React, { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { clientPost } from "../lib/api";

const TRIGGERS = [
  { id: "low-balance", label: "Saldo bajo", path: "/notifications/trigger/low-balance" },
  { id: "allergen-check", label: "Alertas alérgenos", path: "/notifications/trigger/allergen-check" },
  { id: "no-consumption", label: "Sin consumo 12:00", path: "/notifications/trigger/no-consumption" },
  { id: "consumption-ratings", label: "Micro-ratings WhatsApp", path: "/notifications/trigger/consumption-ratings" },
  { id: "weekly-report", label: "Reporte viernes", path: "/notifications/trigger/weekly-report" },
  { id: "process-approvals", label: "Gemini · aprobaciones vencidas", path: "/notifications/trigger/process-approvals" },
];

export const NotificationTriggersPanel: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [busy, setBusy] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<Record<string, string>>({});

  const run = async (t: (typeof TRIGGERS)[0]) => {
    setBusy(t.id);
    try {
      const res = await clientPost(apiBase, t.path, {});
      const sent = res?.sent ?? res?.processed ?? res?.alerts?.length ?? res?.reports?.length ?? "OK";
      setLastResult((s) => ({ ...s, [t.id]: `Ejecutado: ${sent}` }));
    } catch (e: any) {
      setLastResult((s) => ({ ...s, [t.id]: `Error: ${e?.message || "falló"}` }));
    } finally {
      setBusy(null);
    }
  };

  return (
    <ul className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="notification-triggers">
      {TRIGGERS.map((t) => (
        <li key={t.id} className="rounded-xl border border-bio-200 bg-white p-4 flex items-center justify-between gap-3">
          <div>
            <p className="font-medium text-bio-900 text-sm">{t.label}</p>
            {lastResult[t.id] && <p className="text-xs text-bio-500 mt-1">{lastResult[t.id]}</p>}
          </div>
          <button
            type="button"
            onClick={() => run(t)}
            disabled={busy === t.id}
            data-testid={`trigger-run-${t.id}`}
            className="shrink-0 inline-flex items-center gap-1 rounded-lg border border-bio-200 px-3 py-1.5 text-xs font-medium hover:bg-bio-50 disabled:opacity-50"
          >
            {busy === t.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Ejecutar
          </button>
        </li>
      ))}
    </ul>
  );
};

export default NotificationTriggersPanel;
