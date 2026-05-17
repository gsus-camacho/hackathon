import React, { useEffect, useState } from "react";
import { Bell, BellOff, Check, Loader2, ShieldAlert, TrendingDown, Trophy, Sparkles, Tag } from "lucide-react";
import { clientGet, clientPost } from "../lib/api";

interface Notification {
  id: string;
  kind: string;
  recipient_phone: string;
  recipient_name?: string;
  message: string;
  status: string;
  read: boolean;
  created_at: string;
  read_at?: string;
}

const kindIcon: Record<string, React.ComponentType<{ className?: string }>> = {
  allergen_alert: ShieldAlert,
  low_balance: TrendingDown,
  package_offer: Tag,
  meal_plan_reward: Trophy,
  daily_report: Sparkles,
};

const kindColor: Record<string, string> = {
  allergen_alert: "bg-red-50 text-danger",
  low_balance: "bg-amber-50 text-warn",
  package_offer: "bg-brand-soft text-brand",
  meal_plan_reward: "bg-emerald-50 text-ok",
  daily_report: "bg-bio-100 text-bio-700",
  custom: "bg-bio-100 text-bio-700",
};

const kindLabel: Record<string, string> = {
  allergen_alert: "Alerta alérgeno",
  low_balance: "Saldo bajo",
  package_offer: "Oferta paquete",
  meal_plan_reward: "Recompensa plan",
  daily_report: "Reporte diario",
  weekly_nutrition: "Reporte semanal",
  custom: "Mensaje",
};

export const InboxPanel: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [filter, setFilter] = useState<"all" | "unread" | "read">("unread");
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [unread, setUnread] = useState(0);

  const load = async (f = filter) => {
    setLoading(true);
    try {
      const readParam = f === "all" ? "" : `?read=${f === "read"}`;
      const [data, uc] = await Promise.all([
        clientGet(apiBase, `/notifications/${readParam}${readParam ? "&limit=100" : "?limit=100"}`),
        clientGet(apiBase, "/notifications/unread-count"),
      ]);
      setItems(data || []);
      setUnread(uc?.count || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(filter); }, [filter, apiBase]);

  const mark = async (id: string, read: boolean) => {
    const action = read ? "read" : "unread";
    await clientPost(apiBase, `/notifications/${id}/${action}`);
    load();
  };

  const markAll = async () => {
    await clientPost(apiBase, "/notifications/read-all");
    load();
  };

  return (
    <div data-testid="inbox-panel">
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div className="flex items-center gap-1.5 rounded-lg border border-bio-200 bg-white p-1">
          {(["unread", "read", "all"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-3 py-1.5 rounded-md transition-colors ${
                filter === f ? "bg-bio-900 text-white" : "text-bio-700 hover:bg-bio-100"
              }`}
              data-testid={`filter-${f}`}
            >
              {f === "unread" ? `Sin leer ${unread ? `(${unread})` : ""}` : f === "read" ? "Leídas" : "Todas"}
            </button>
          ))}
        </div>
        {unread > 0 && (
          <button
            onClick={markAll}
            className="inline-flex items-center gap-2 text-xs rounded-lg bg-brand hover:bg-brand-hover text-white px-3 py-1.5 transition-colors"
            data-testid="mark-all-read-btn"
          >
            <Check className="h-3.5 w-3.5" /> Marcar todo como leído
          </button>
        )}
      </div>

      {loading ? (
        <div className="rounded-xl border border-bio-200 bg-white p-12 text-center" data-testid="inbox-loading">
          <Loader2 className="h-5 w-5 text-bio-500 animate-spin mx-auto" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center" data-testid="inbox-empty">
          <Bell className="h-7 w-7 text-bio-500 mx-auto mb-2" />
          <p className="text-sm text-bio-500">No hay notificaciones {filter === "unread" ? "sin leer" : ""}.</p>
        </div>
      ) : (
        <ul className="space-y-2" data-testid="inbox-list">
          {items.map((n) => {
            const Icon = kindIcon[n.kind] || Bell;
            const colorCls = kindColor[n.kind] || "bg-bio-100 text-bio-700";
            return (
              <li
                key={n.id}
                className={`rounded-xl border p-4 transition-all duration-200 ${
                  n.read ? "border-bio-200 bg-white" : "border-brand/30 bg-brand-soft/30"
                }`}
                data-testid={`inbox-item-${n.id}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`rounded-lg p-2 flex-shrink-0 ${colorCls}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-bio-100 text-bio-700">
                          {kindLabel[n.kind] || n.kind}
                        </span>
                        {!n.read && <span className="w-2 h-2 rounded-full bg-brand animate-pulse-soft" />}
                      </div>
                      <span className="text-[10px] font-mono text-bio-500">
                        {n.created_at.slice(0, 16).replace("T", " ")}
                      </span>
                    </div>
                    <p className="text-sm text-bio-900 mt-2 whitespace-pre-wrap">{n.message}</p>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="font-mono text-bio-500">{n.recipient_phone}</span>
                      <button
                        onClick={() => mark(n.id, !n.read)}
                        className="inline-flex items-center gap-1 text-xs text-brand hover:text-brand-hover transition-colors"
                        data-testid={`toggle-read-${n.id}`}
                      >
                        {n.read ? <BellOff className="h-3 w-3" /> : <Check className="h-3 w-3" />}
                        {n.read ? "Marcar sin leer" : "Marcar leída"}
                      </button>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default InboxPanel;
