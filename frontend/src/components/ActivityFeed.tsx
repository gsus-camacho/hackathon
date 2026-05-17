import React from "react";
import { Bell, ShoppingBag } from "lucide-react";

interface Item {
  timestamp: string;
  kind: string;
  title: string;
  detail: string;
}

export const ActivityFeed: React.FC<{ items: Item[] }> = ({ items }) => {
  if (!items?.length) {
    return (
      <div className="text-sm text-bio-500" data-testid="activity-empty">
        Sin actividad reciente.
      </div>
    );
  }
  return (
    <ul className="divide-y divide-bio-200" data-testid="activity-feed">
      {items.map((it, i) => (
        <li key={i} className="py-3 flex items-start gap-3">
          <div
            className={`mt-0.5 rounded-full p-2 ${
              it.kind === "venta" ? "bg-brand-soft text-brand" : "bg-emerald-50 text-ok"
            }`}
          >
            {it.kind === "venta" ? (
              <ShoppingBag className="h-3.5 w-3.5" />
            ) : (
              <Bell className="h-3.5 w-3.5" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm font-medium text-bio-900 truncate">{it.title}</span>
              <span className="text-[10px] font-mono text-bio-500 whitespace-nowrap">
                {it.timestamp.slice(0, 10)}
              </span>
            </div>
            <p className="text-xs text-bio-500 truncate">{it.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
};

export default ActivityFeed;
