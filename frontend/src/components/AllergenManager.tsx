import React, { useState } from "react";
import { ShieldAlert, Plus } from "lucide-react";
import { clientPost } from "../lib/api";

interface Allergen {
  id: string;
  usuario_identificacion: string;
  nombre_estudiante?: string;
  identificacion_padre?: string;
  nit_colegio?: string;
  allergens: string[];
  notes?: string;
}

export const AllergenManager: React.FC<{ apiBase: string; initial: Allergen[] }> = ({ apiBase, initial }) => {
  const [list, setList] = useState<Allergen[]>(initial || []);
  const [form, setForm] = useState({
    usuario_identificacion: "",
    nombre_estudiante: "",
    identificacion_padre: "",
    nit_colegio: "",
    allergens: "",
    notes: "",
  });
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.usuario_identificacion || !form.allergens) return;
    setBusy(true);
    try {
      const data = await clientPost(apiBase, "/recommendations/allergens", {
        ...form,
        allergens: form.allergens.split(",").map((x) => x.trim()).filter(Boolean),
      });
      setList((c) => [data, ...c]);
      setForm({
        usuario_identificacion: "",
        nombre_estudiante: "",
        identificacion_padre: "",
        nit_colegio: "",
        allergens: "",
        notes: "",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-5 gap-6" data-testid="allergen-manager">
      <form
        onSubmit={submit}
        className="lg:col-span-2 rounded-xl border border-bio-200 bg-white p-5 space-y-3 h-fit"
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="rounded-lg bg-red-50 text-danger p-2">
            <ShieldAlert className="h-4 w-4" />
          </div>
          <h3 className="font-heading font-semibold text-bio-900">Registrar alergeno</h3>
        </div>
        {[
          ["usuario_identificacion", "ID Estudiante *", true],
          ["nombre_estudiante", "Nombre del estudiante", false],
          ["identificacion_padre", "ID Acudiente", false],
          ["nit_colegio", "NIT Colegio", false],
          ["allergens", "Alergenos (separados por coma) *", true],
        ].map(([k, label, req]) => (
          <div key={k as string}>
            <label className="text-xs font-mono uppercase tracking-wider text-bio-500">
              {label}
            </label>
            <input
              required={req as boolean}
              value={(form as any)[k as string]}
              onChange={(e) => setForm({ ...form, [k as string]: e.target.value })}
              className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
              data-testid={`allergen-${k as string}`}
            />
          </div>
        ))}
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Notas</label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            rows={2}
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="allergen-notes"
          />
        </div>
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-bio-900 hover:bg-bio-800 text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="allergen-submit-btn"
        >
          <Plus className="h-4 w-4" /> {busy ? "Guardando…" : "Registrar"}
        </button>
      </form>
      <div className="lg:col-span-3">
        <h3 className="font-heading font-semibold text-bio-900 mb-3">Perfiles registrados</h3>
        {list.length === 0 ? (
          <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
            <p className="text-sm text-bio-500">Aún no hay alergenos registrados.</p>
          </div>
        ) : (
          <ul className="space-y-3" data-testid="allergen-list">
            {list.map((a) => (
              <li
                key={a.id}
                className="rounded-xl border border-bio-200 bg-white p-4 hover:shadow-card transition-all"
                data-testid={`allergen-row-${a.id}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium text-bio-900">{a.nombre_estudiante || a.usuario_identificacion}</div>
                    <div className="text-xs text-bio-500 font-mono">{a.usuario_identificacion}</div>
                  </div>
                  <div className="flex flex-wrap gap-1 justify-end max-w-[60%]">
                    {a.allergens.map((al, i) => (
                      <span key={i} className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-red-50 text-danger">
                        {al}
                      </span>
                    ))}
                  </div>
                </div>
                {a.notes && <p className="text-xs text-bio-500 mt-2">{a.notes}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default AllergenManager;
