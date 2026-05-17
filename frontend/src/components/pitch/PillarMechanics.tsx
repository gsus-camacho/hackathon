import React from "react";

export interface MechanicItem {
  label: string;
  body: string;
  variant?: "default" | "success";
}

export const PillarMechanics: React.FC<{ items: MechanicItem[]; testId?: string }> = ({
  items,
  testId = "pillar-mechanics",
}) => (
  <ul className="space-y-3" data-testid={testId}>
    {items.map((item) => (
      <li
        key={item.label}
        className={`rounded-xl border p-4 ${
          item.variant === "success"
            ? "border-emerald-200 bg-emerald-50/80"
            : "border-bio-200 bg-bio-50/50"
        }`}
      >
        <span
          className={`text-[10px] font-mono uppercase tracking-wide ${
            item.variant === "success" ? "text-ok" : "text-bio-500"
          }`}
        >
          {item.label}
        </span>
        <p
          className={`text-sm font-medium mt-2 leading-relaxed ${
            item.variant === "success" ? "text-ok" : "text-bio-900"
          }`}
        >
          {item.body}
        </p>
      </li>
    ))}
  </ul>
);

export default PillarMechanics;
