import React, { useState } from "react";
import { Plus, ShieldAlert, Trash2, Phone, GraduationCap, Hash } from "lucide-react";
import { clientDelete, clientPost } from "../lib/api";

interface Hijo {
  id: string;
  usuario_identificacion: string;
  nombre_estudiante: string;
  identificacion_padre?: string;
  nombre_padre?: string;
  nit_colegio?: string;
  colegio?: string;
  grado?: string;
  allergens: string[];
  notes: string;
  parent_phone?: string;
}

export const HijosPanel: React.FC<{ apiBase: string; initial: Hijo[] }> = ({ apiBase, initial }) => {
  const [list, setList] = useState<Hijo[]>(initial || []);
  const [form, setForm] = useState({ usuario_identificacion: "", allergens: "", notes: "", parent_phone: "" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.usuario_identificacion) return;
    setBusy(true);
    setErr(null);
    try {
      const doc: Hijo = await clientPost(apiBase, "/hijos/", {
        usuario_identificacion: form.usuario_identificacion.trim(),
        allergens: form.allergens.split(",").map((s) => s.trim()).filter(Boolean),
        notes: form.notes,
        parent_phone: form.parent_phone || undefined,
      });
      setList((c) => [doc, ...c]);
      setForm({ usuario_identificacion: "", allergens: "", notes: "", parent_phone: "" });
    } catch (e: any) {
      setErr(e?.message || "Error registrando");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm("¿Eliminar este perfil?")) return;
    await clientDelete(apiBase, `/hijos/${id}`);
    setList((c) => c.filter((h) => h.id !== id));
  };

  return (
    <div className="grid lg:grid-cols-5 gap-6" data-testid="hijos-panel">
      <form onSubmit={submit} className="lg:col-span-2 rounded-xl border border-bio-200 bg-white p-5 space-y-3 h-fit">
        <div className="flex items-center gap-2 mb-1">
          <div className="rounded-lg bg-brand-soft text-brand p-2"><Plus className="h-4 w-4" /></div>
          <h3 className="font-heading font-semibold text-bio-900">Configurar nuevo hijo</h3>
        </div>
        <p className="text-xs text-bio-500">Auto-completa nombre, padre y colegio desde Biofood al ingresar el ID.</p>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">ID Estudiante *</label>
          <input
            required
            value={form.usuario_identificacion}
            onChange={(e) => setForm({ ...form, usuario_identificacion: e.target.value })}
            placeholder="0010066601"
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="hijo-input-id"
          />
        </div>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Alergenos (coma)</label>
          <input
            value={form.allergens}
            onChange={(e) => setForm({ ...form, allergens: e.target.value })}
            placeholder="mani, lactosa, gluten"
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="hijo-input-allergens"
          />
        </div>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Teléfono acudiente (WhatsApp)</label>
          <input
            value={form.parent_phone}
            onChange={(e) => setForm({ ...form, parent_phone: e.target.value })}
            placeholder="+573004280744"
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="hijo-input-phone"
          />
        </div>
        <div>
          <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Notas</label>
          <textarea
            rows={3}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Observaciones, restricciones, contactos de emergencia..."
            className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
            data-testid="hijo-input-notes"
          />
        </div>
        {err && <div className="text-xs text-danger bg-red-50 rounded-lg p-2" data-testid="hijo-error">{err}</div>}
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="hijo-submit-btn"
        >
          <Plus className="h-4 w-4" /> {busy ? "Guardando…" : "Configurar hijo"}
        </button>
      </form>

      <div className="lg:col-span-3">
        <h3 className="font-heading font-semibold text-bio-900 mb-3">{list.length} hijo{list.length === 1 ? "" : "s"} configurado{list.length === 1 ? "" : "s"}</h3>
        {list.length === 0 ? (
          <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center">
            <p className="text-sm text-bio-500">Aún no has configurado ningún hijo.</p>
          </div>
        ) : (
          <ul className="grid sm:grid-cols-2 gap-4" data-testid="hijos-list">
            {list.map((h) => (
              <li
                key={h.id}
                className="rounded-xl border border-bio-200 bg-white p-5 hover:-translate-y-0.5 hover:shadow-card transition-all duration-200 animate-fade-up"
                data-testid={`hijo-card-${h.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-12 h-12 rounded-full bg-brand-soft text-brand grid place-items-center font-heading font-semibold text-lg flex-shrink-0">
                      {h.nombre_estudiante.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <div className="font-heading font-semibold text-bio-900 truncate">{h.nombre_estudiante}</div>
                      <div className="text-xs font-mono text-bio-500 flex items-center gap-1">
                        <Hash className="h-3 w-3" /> {h.usuario_identificacion}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => remove(h.id)}
                    className="text-bio-500 hover:text-danger transition-colors"
                    data-testid={`hijo-delete-${h.id}`}
                    aria-label="Eliminar"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                {h.colegio && (
                  <div className="mt-3 text-xs text-bio-500 flex items-center gap-1.5">
                    <GraduationCap className="h-3.5 w-3.5" /> {h.colegio}
                  </div>
                )}
                {h.parent_phone && (
                  <div className="text-xs text-bio-500 font-mono flex items-center gap-1.5 mt-1">
                    <Phone className="h-3.5 w-3.5" /> {h.parent_phone}
                  </div>
                )}
                {h.allergens?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-bio-100">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider font-mono text-danger mb-2">
                      <ShieldAlert className="h-3 w-3" /> Alergenos
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {h.allergens.map((a, i) => (
                        <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-50 text-danger">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {h.notes && <p className="text-xs text-bio-500 mt-3 italic line-clamp-3">{h.notes}</p>}
                <a
                  href={`/planifications?hijo=${h.id}`}
                  className="mt-3 inline-flex items-center justify-center w-full text-xs font-medium px-3 py-2 rounded-lg bg-bio-50 hover:bg-bio-100 text-bio-700 transition-colors"
                  data-testid={`hijo-plan-${h.id}`}
                >
                  Plan semanal →
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default HijosPanel;
