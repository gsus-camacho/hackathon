import React, { useState } from "react";
import { Sparkles } from "lucide-react";

const PREFS = [
  { id: "gluten", label: "Sin gluten", defaultOn: true },
  { id: "vegan", label: "Vegano", defaultOn: false },
  { id: "lactose", label: "Sin lactosa", defaultOn: true },
  { id: "nuts", label: "Sin frutos secos", defaultOn: true },
  { id: "avocado", label: "Sin aguacate", defaultOn: false },
  { id: "egg", label: "Sin huevo", defaultOn: false },
];

export const DietaryPreferencesDemo: React.FC = () => {
  const [on, setOn] = useState<Record<string, boolean>>(
    Object.fromEntries(PREFS.map((p) => [p.id, p.defaultOn]))
  );

  return (
    <section
      className="rounded-2xl border border-bio-200 bg-white overflow-hidden max-w-sm mx-auto shadow-card"
      data-testid="dietary-preferences-demo"
    >
      <header className="bg-bio-50 border-b border-bio-200 px-4 py-3 flex items-center gap-3">
        <span className="w-10 h-10 rounded-full bg-brand-soft text-brand font-semibold text-sm grid place-items-center">
          TR
        </span>
        <span>
          <span className="block font-medium text-bio-900">Tomás Rodríguez</span>
          <span className="block text-xs text-bio-500 font-mono">5° A · ID 0042</span>
        </span>
      </header>
      <section className="p-4">
        <h3 className="text-xs font-mono uppercase tracking-wide text-bio-500 mb-3">
          Preferencias alimentarias
        </h3>
        <ul className="space-y-2">
          {PREFS.map((p) => (
            <li key={p.id} className="flex items-center justify-between text-sm text-bio-800">
              <span>{p.label}</span>
              <button
                type="button"
                role="switch"
                aria-checked={on[p.id]}
                data-testid={`pref-toggle-${p.id}`}
                onClick={() => setOn((s) => ({ ...s, [p.id]: !s[p.id] }))}
                className={`w-11 h-6 rounded-full transition-colors relative ${
                  on[p.id] ? "bg-brand" : "bg-bio-200"
                }`}
              >
                <span
                  className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                    on[p.id] ? "left-[22px]" : "left-0.5"
                  }`}
                />
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-4 flex items-start gap-2 text-xs text-bio-600 bg-brand-soft/40 border border-brand/20 rounded-lg p-3">
          <Sparkles className="h-4 w-4 text-brand shrink-0 mt-0.5" />
          <span>
            <strong className="text-bio-900">Gemini API</strong> analiza nuevos productos en segundo plano y bloquea
            por defecto si hay riesgo.
          </span>
        </p>
      </section>
    </section>
  );
};

export default DietaryPreferencesDemo;
