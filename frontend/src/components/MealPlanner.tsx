import React, { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, Calendar, Target, Trophy, Loader2, AlertTriangle, ShieldCheck, CheckCircle2 } from "lucide-react";
import { clientDelete, clientGet, clientPost } from "../lib/api";

interface Hijo { id: string; nombre_estudiante: string; usuario_identificacion: string; allergens?: string[]; }
interface MealItem { day: number; product_name: string; quantity: number; unit_price: number; }
interface MealPlan {
  id: string;
  hijo_id: string;
  week_start: string;
  minimum_budget: number;
  items: MealItem[];
  current_total: number;
  goal_met: boolean;
  reward?: string;
  _allergen_warning?: string[];
}

const DAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const fmt = (n: number) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n);

function isoMonday(): string {
  const d = new Date();
  const day = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - day);
  return d.toISOString().slice(0, 10);
}

export const MealPlanner: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [hijos, setHijos] = useState<Hijo[]>([]);
  const [selectedHijo, setSelectedHijo] = useState<string>("");
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [products, setProducts] = useState<{ name: string; revenue: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newItem, setNewItem] = useState({ day: 0, product_name: "", quantity: 1, unit_price: 0 });
  const [budget, setBudget] = useState(50000);
  const [allergenError, setAllergenError] = useState<string | null>(null);
  const [allergenWarning, setAllergenWarning] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const [hjs, prods] = await Promise.all([
        clientGet(apiBase, "/hijos/").then((data) => data || []).catch(() => []),
        clientGet(apiBase, "/statistics/top-products?limit=15").then((data) => data || []).catch(() => []),
      ]);
      setHijos(hjs || []);
      setProducts(prods || []);
      const url = new URL(window.location.href);
      const h = url.searchParams.get("hijo");
      if (h && hjs?.find((x: Hijo) => x.id === h)) setSelectedHijo(h);
      else if (hjs?.length) setSelectedHijo(hjs[0].id);
      setLoading(false);
    })();
  }, [apiBase]);

  useEffect(() => {
    if (!selectedHijo) return;
    (async () => {
      const data = await clientGet(apiBase, `/planifications/hijos/${selectedHijo}/active-plan`);
      setPlan(data || null);
      if (data?.minimum_budget) setBudget(data.minimum_budget);
    })();
  }, [selectedHijo, apiBase]);

  const createPlan = async () => {
    if (!selectedHijo) return;
    setAdding(true);
    try {
      const data = await clientPost(apiBase, "/planifications/plans", {
        hijo_id: selectedHijo,
        week_start: isoMonday(),
        minimum_budget: budget,
        items: [],
      });
      setPlan(data);
    } finally {
      setAdding(false);
    }
  };

  const addItem = async () => {
    if (!plan || !newItem.product_name || newItem.unit_price <= 0) return;
    setAdding(true);
    setAllergenError(null);
    setAllergenWarning(null);
    try {
      const data = await clientPost(apiBase, `/planifications/plans/${plan.id}/items`, newItem);
      setPlan(data);
      setNewItem({ day: 0, product_name: "", quantity: 1, unit_price: 0 });
      if (data._allergen_warning) {
        setAllergenWarning(`Producto compatible, pero revisa: ${data._allergen_warning.join(", ")}`);
      }
    } catch (err: any) {
      if (err?.status === 409) {
        setAllergenError(err?.message || "El producto fue bloqueado por seguridad — contiene alérgenos incompatibles.");
      } else {
        setAllergenError("Error al agregar producto. Intenta de nuevo.");
      }
    } finally {
      setAdding(false);
    }
  };

  const removeItem = async (idx: number) => {
    if (!plan) return;
    setAllergenError(null);
    setAllergenWarning(null);
    try {
      const data = await clientDelete(apiBase, `/planifications/plans/${plan.id}/items/${idx}`);
      setPlan(data as MealPlan);
    } catch (err) {
      setAllergenError("Error al eliminar producto.");
    }
  };

  const progress = useMemo(() => {
    if (!plan || !plan.minimum_budget) return 0;
    return Math.min(100, (plan.current_total / plan.minimum_budget) * 100);
  }, [plan]);

  if (loading) {
    return (
      <div className="rounded-xl border border-bio-200 bg-white p-12 text-center" data-testid="meal-loading">
        <Loader2 className="h-6 w-6 text-bio-500 animate-spin mx-auto mb-3" />
        <p className="text-sm text-bio-500">Cargando…</p>
      </div>
    );
  }

  if (!hijos.length) {
    return (
      <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center" data-testid="meal-no-hijos">
        <p className="text-sm text-bio-500 mb-3">No hay hijos configurados todavía.</p>
        <a href="/hijos" className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium transition-colors" data-testid="cta-go-hijos">
          Configurar mi primer hijo →
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="meal-planner">
      {/* Hijo selector */}
      <div className="flex flex-wrap gap-2" data-testid="hijo-selector">
        {hijos.map((h) => (
          <button
            key={h.id}
            onClick={() => setSelectedHijo(h.id)}
            className={`text-sm px-4 py-2 rounded-lg transition-colors ${
              selectedHijo === h.id
                ? "bg-bio-900 text-white"
                : "bg-white border border-bio-200 text-bio-700 hover:bg-bio-50"
            }`}
            data-testid={`select-hijo-${h.id}`}
          >
            {h.nombre_estudiante}
          </button>
        ))}
      </div>

      {!plan ? (
        <div className="rounded-xl border border-bio-200 bg-white p-6" data-testid="meal-create">
          <div className="flex items-center gap-2 mb-3">
            <Calendar className="h-4 w-4 text-brand" />
            <h3 className="font-heading font-semibold text-bio-900">Crear plan semanal</h3>
          </div>
          <p className="text-sm text-bio-500 mb-4">
            Define un presupuesto mínimo de consumo. Al alcanzarlo, el hijo desbloquea una recompensa 🎁
          </p>
          <div className="flex items-end gap-3">
            <div className="flex-1 max-w-xs">
              <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Presupuesto mínimo</label>
              <input
                type="number"
                min={1000}
                step={1000}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
                className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm font-mono"
                data-testid="meal-budget-input"
              />
            </div>
            <button
              onClick={createPlan}
              disabled={adding}
              className="rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
              data-testid="meal-create-btn"
            >
              {adding ? "Creando…" : "Crear plan"}
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Progress card */}
          <div className="rounded-xl border border-bio-200 bg-white p-5" data-testid="meal-progress">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-brand" />
                  <h3 className="font-heading font-semibold text-bio-900">Progreso semanal</h3>
                </div>
                <p className="text-xs text-bio-500 mt-1">Semana iniciando {plan.week_start}</p>
              </div>
              <div className="text-right">
                <div className="font-heading text-2xl font-semibold text-bio-900" data-testid="meal-total">
                  {fmt(plan.current_total)}
                </div>
                <div className="text-xs text-bio-500 font-mono">meta {fmt(plan.minimum_budget)}</div>
              </div>
            </div>
            <div className="mt-4 h-3 rounded-full bg-bio-100 overflow-hidden" data-testid="meal-progress-bar">
              <div
                className={`h-full rounded-full transition-all duration-500 ${plan.goal_met ? "bg-ok" : "bg-brand"}`}
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="font-mono text-bio-500">{progress.toFixed(0)}% completado</span>
              {plan.goal_met && plan.reward && (
                <span className="inline-flex items-center gap-1 text-ok font-medium" data-testid="meal-reward">
                  <Trophy className="h-3.5 w-3.5" /> {plan.reward}
                </span>
              )}
            </div>
          </div>

          {/* Weekly grid */}
          <div className="rounded-xl border border-bio-200 bg-white p-5">
            <h3 className="font-heading font-semibold text-bio-900 mb-3">Asignación semanal</h3>
            <div className="grid grid-cols-7 gap-2" data-testid="meal-week-grid">
              {DAYS.map((day, idx) => {
                const dayItems = plan.items
                  .map((item, index) => ({ item, index }))
                  .filter(({ item }) => item.day === idx);
                return (
                  <div key={idx} className="rounded-lg border border-bio-200 p-2 min-h-[120px]" data-testid={`day-${idx}`}>
                    <div className="text-[10px] uppercase tracking-wider font-mono text-bio-500 mb-2">{day}</div>
                    <ul className="space-y-1.5">
                      {dayItems.map(({ item, index }, i) => (
                        <li key={`${index}-${item.product_name}`} className="group bg-brand-soft text-bio-900 rounded px-2 py-1 text-[11px]" data-testid={`day-${idx}-item-${i}`}>
                          <div className="flex items-start justify-between gap-1">
                            <span className="truncate">{item.product_name}</span>
                            <button onClick={() => removeItem(index)} className="opacity-0 group-hover:opacity-100 text-danger transition-opacity">
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                          <div className="text-[10px] font-mono text-bio-500">x{item.quantity} · {fmt(item.unit_price * item.quantity)}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Allergen error / warning banner */}
          {allergenError && (
            <div className="rounded-xl border border-danger/30 bg-danger-soft p-4 flex items-start gap-3" data-testid="allergen-error">
              <AlertTriangle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-danger">⛔ Producto bloqueado por seguridad</p>
                <p className="text-xs text-danger/80 mt-1">{allergenError}</p>
                <p className="text-xs text-danger/60 mt-1 italic">Pilar 2 · Seguridad nutricional automatizada — Bloqueo por defecto ante riesgo</p>
              </div>
            </div>
          )}
          {allergenWarning && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 flex items-start gap-3" data-testid="allergen-warning">
              <ShieldCheck className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">⚠️ Precaución</p>
                <p className="text-xs text-amber-700 mt-1">{allergenWarning}</p>
              </div>
            </div>
          )}

          {/* Add item */}
          <div className="rounded-xl border border-bio-200 bg-white p-5" data-testid="meal-add">
            <h3 className="font-heading font-semibold text-bio-900 mb-3">Asignar producto</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div>
                <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Día</label>
                <select
                  value={newItem.day}
                  onChange={(e) => {
                    setNewItem({ ...newItem, day: Number(e.target.value) });
                    setAllergenError(null);
                    setAllergenWarning(null);
                  }}
                  className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm"
                  data-testid="meal-day-select"
                >
                  {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Producto</label>
                <select
                  value={newItem.product_name}
                  onChange={(e) => {
                    const prod = products.find((p) => p.name === e.target.value);
                    setNewItem({ ...newItem, product_name: e.target.value, unit_price: prod ? Math.round(prod.revenue / 200) : 0 });
                    setAllergenError(null);
                    setAllergenWarning(null);
                  }}
                  className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm"
                  data-testid="meal-product-select"
                >
                  <option value="">Selecciona…</option>
                  {products.map((p) => <option key={p.name} value={p.name}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-mono uppercase tracking-wider text-bio-500">Precio</label>
                <input
                  type="number"
                  value={newItem.unit_price}
                  onChange={(e) => {
                    setNewItem({ ...newItem, unit_price: Number(e.target.value) });
                    setAllergenError(null);
                  }}
                  className="mt-1 w-full rounded-lg border border-bio-200 bg-white px-3 py-2 text-sm font-mono"
                  data-testid="meal-price-input"
                />
              </div>
            </div>
            <div className="flex items-center gap-3 mt-4">
              <button
                onClick={addItem}
                disabled={adding || !newItem.product_name}
                className="inline-flex items-center gap-2 rounded-lg bg-brand hover:bg-brand-hover text-white px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors"
                data-testid="meal-add-btn"
              >
                <Plus className="h-4 w-4" /> {adding ? "Agregando…" : "Agregar producto"}
              </button>
              <span className="text-[10px] text-bio-400 font-mono">🔒 Validación Pilar 2 activa</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MealPlanner;
