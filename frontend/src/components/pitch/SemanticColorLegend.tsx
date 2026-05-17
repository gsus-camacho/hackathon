import React from "react";

const swatches = [
  { label: "primary · acciones", className: "bg-brand text-white" },
  { label: "success · permitir", className: "bg-ok text-white" },
  { label: "error · bloquear", className: "bg-danger text-white" },
  { label: "warn · revisar", className: "bg-warn text-white" },
];

export const SemanticColorLegend: React.FC = () => (
  <section data-testid="semantic-color-legend">
    <p className="text-[10px] font-mono uppercase tracking-wide text-bio-500 mb-3">
      Color semántico sobre identidad Biofood
    </p>
    <ul className="grid grid-cols-2 md:grid-cols-4 gap-2">
      {swatches.map((s) => (
        <li
          key={s.label}
          className={`rounded-lg px-3 py-2 text-[11px] font-mono ${s.className}`}
        >
          {s.label}
        </li>
      ))}
    </ul>
    <p className="text-xs text-bio-500 mt-3">
      Tres pantallas nuevas dentro del mismo producto — curva de aprendizaje mínima para cafetería y padres.
    </p>
  </section>
);

export default SemanticColorLegend;
