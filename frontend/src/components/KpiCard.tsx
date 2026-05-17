import React from "react";
import { cn } from "../lib/cn";
import { ArrowUpRight, type LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaTone?: "positive" | "negative" | "neutral";
  icon?: LucideIcon;
  testId?: string;
  accent?: "brand" | "danger" | "warn" | "ok";
}

const accentMap: Record<string, string> = {
  brand: "bg-brand-soft text-brand",
  danger: "bg-red-50 text-danger",
  warn: "bg-amber-50 text-warn",
  ok: "bg-emerald-50 text-ok",
};

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  delta,
  deltaTone = "neutral",
  icon: Icon,
  testId,
  accent = "brand",
}) => {
  return (
    <div
      data-testid={testId}
      className="group relative rounded-xl border border-bio-200 bg-white p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card animate-fade-up"
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-bio-500 font-mono">{label}</div>
          <div className="mt-2 font-heading text-3xl font-semibold text-bio-900 tracking-tight">
            {value}
          </div>
          {delta && (
            <div
              className={cn(
                "mt-1 inline-flex items-center gap-1 text-xs font-mono",
                deltaTone === "positive" && "text-ok",
                deltaTone === "negative" && "text-danger",
                deltaTone === "neutral" && "text-bio-500"
              )}
            >
              <ArrowUpRight className="h-3.5 w-3.5" />
              {delta}
            </div>
          )}
        </div>
        {Icon && (
          <div className={cn("rounded-lg p-2.5", accentMap[accent])}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  );
};

export default KpiCard;
