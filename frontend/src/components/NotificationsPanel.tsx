import React, { useState } from "react";
import { Bell, Send } from "lucide-react";

interface Notification {
  id: string;
  kind: string;
  recipient_phone: string;
  message: string;
  status: string;
  error?: string;
  created_at?: string;
}

const kindColor: Record<string, string> = {
  allergen_alert: "bg-red-50 text-danger",
  low_balance: "bg-amber-50 text-warn",
  package_offer: "bg-brand-soft text-brand",
  daily_report: "bg-emerald-50 text-ok",
  custom: "bg-bio-100 text-bio-700",
};

export const NotificationsPanel: React.FC<{ apiBase: string; initial: Notification[] }> = ({
  apiBase,
  initial,
}) => {
  const [list, setList] = useState<Notification[]>(initial || []);
  const [phone, setPhone] = useState("whatsapp:+573004280744");
  const [body, setBody] = useState("Hola, este es un mensaje de prueba desde BioAlert+.");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(`${apiBase}/api/notifications/send`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ to: phone, body, kind: "custom" }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || res.statusText);
      }
      const data: Notification = await res.json();
      setList((c) => [data, ...c]);
      setBody("");
    } catch (e: any) {
      setErr(e?.message || "Error enviando");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-5 gap-6" data-testid="notifications-panel">
      <form onSubmit={send} className="lg:col-span-2 rounded-xl border border-bio-200 bg-white p-5 space-y-3 h-fit">
        <div className="flex items-center gap-2 mb-2">
          <div className="rounded-lg bg-brand-soft text-brand p-2">
            <Bell className="h-4 w-4" />
          </div>
          <h3 className="font-heading font-semibold text-bio-900">Enviar WhatsApp</h3>
        </div>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Destinatario</label>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="notif-phone"
          />
        </div>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Mensaje</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="notif-body"
          />
        </div>
        {err && <div className="text-xs text-danger bg-red-50 rounded-lg p-3" data-testid="notif-error">{err}</div>}
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="notif-send-btn"
        >
          <Send className="h-4 w-4" /> {busy ? "Enviando…" : "Enviar"}
        </button>
        <p className="text-[10px] text-bio-500 mt-2">
          Twilio Sandbox: el destinatario debe haber escrito el código de sandbox antes.
        </p>
      </form>

      <div className="lg:col-span-3">
        <h3 className="font-heading font-semibold text-bio-900 mb-3">Bandeja de salida</h3>
        {list.length === 0 ? (
          <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
            <p className="text-sm text-bio-500">No hay envíos aún.</p>
          </div>
        ) : (
          <ul className="space-y-2" data-testid="notif-list">
            {list.map((n) => (
              <li
                key={n.id}
                className="rounded-xl border border-bio-200 bg-white p-4"
                data-testid={`notif-row-${n.id}`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded ${kindColor[n.kind] || "bg-bio-100"}`}>
                    {n.kind}
                  </span>
                  <span className="text-[10px] font-mono text-bio-500">
                    {n.status} · {n.created_at?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
                <div className="text-xs text-bio-500 font-mono mt-1">{n.recipient_phone}</div>
                <p className="text-sm text-bio-700 mt-2 whitespace-pre-wrap">{n.message}</p>
                {n.error && <p className="text-xs text-danger mt-1">{n.error}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default NotificationsPanel;
