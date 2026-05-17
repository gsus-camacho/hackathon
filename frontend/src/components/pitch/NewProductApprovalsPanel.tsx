import React, { useState } from "react";
import { Check, X } from "lucide-react";

const PENDING = [
  { id: "1", product: "Brownie de chocolate", student: "Tomás R.", school: "Colegio Andino", sent: "hace 2h" },
  { id: "2", product: "Barra proteica vainilla", student: "Sofía C.", school: "Gimnasio Moderno", sent: "hace 5h" },
];

export const NewProductApprovalsPanel: React.FC = () => {
  const [items, setItems] = useState(PENDING);

  const resolve = (id: string, action: "allow" | "block") => {
    setItems((list) => list.filter((i) => i.id !== id));
  };

  if (items.length === 0) {
    return (
      <p className="text-sm text-bio-500 py-8 text-center rounded-xl border border-dashed border-bio-200" data-testid="approvals-empty">
        Cola vacía — todas las solicitudes de productos nuevos fueron resueltas.
      </p>
    );
  }

  return (
    <ul className="space-y-3" data-testid="new-product-approvals">
      {items.map((item) => (
        <li key={item.id} className="rounded-xl border border-bio-200 bg-white p-4">
          <p className="text-[10px] font-mono uppercase tracking-wide text-brand">Nuevo producto · WhatsApp</p>
          <p className="font-medium text-bio-900 mt-1">{item.product}</p>
          <p className="text-xs text-bio-500 mt-1">
            {item.student} · {item.school} · enviado {item.sent}
          </p>
          <p className="text-xs text-bio-500 mt-2 italic">
            Sin respuesta del padre → Pilar 2 delega a Gemini (bloqueo conservador).
          </p>
          <span className="flex gap-2 mt-3">
            <button
              type="button"
              data-testid={`approve-${item.id}`}
              onClick={() => resolve(item.id, "allow")}
              className="inline-flex items-center gap-1.5 rounded-lg bg-ok/10 text-ok border border-ok/30 px-3 py-1.5 text-sm font-medium hover:bg-ok/20"
            >
              <Check className="h-4 w-4" /> Permitir
            </button>
            <button
              type="button"
              data-testid={`block-${item.id}`}
              onClick={() => resolve(item.id, "block")}
              className="inline-flex items-center gap-1.5 rounded-lg bg-red-50 text-danger border border-red-200 px-3 py-1.5 text-sm font-medium hover:bg-red-100"
            >
              <X className="h-4 w-4" /> Bloquear
            </button>
          </span>
        </li>
      ))}
    </ul>
  );
};

export default NewProductApprovalsPanel;
