import React from "react";
import { AlertTriangle } from "lucide-react";

interface Student {
  usuario_identificacion: string;
  nombre_estudiante: string;
  nit_colegio?: string;
  current_balance: number;
  avg_daily_spend: number;
  days_remaining: number;
  risk_level: string;
  last_consumption_date?: string;
  last_recharge_date?: string;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n);

const riskClass: Record<string, string> = {
  high: "bg-red-50 text-danger",
  medium: "bg-amber-50 text-warn",
  low: "bg-emerald-50 text-ok",
};

export const AtRiskTable: React.FC<{ students: Student[] }> = ({ students }) => {
  if (!students?.length) {
    return (
      <div className="rounded-xl border border-dashed border-bio-200 p-12 text-center" data-testid="at-risk-empty">
        <AlertTriangle className="h-7 w-7 text-bio-500 mx-auto mb-2" />
        <p className="text-sm text-bio-500">Sin estudiantes en riesgo. ¡Buen trabajo!</p>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-bio-200 bg-white overflow-x-auto" data-testid="at-risk-table">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-[0.18em] text-bio-500 font-mono border-b border-bio-200">
            <th className="px-4 py-3">Estudiante</th>
            <th className="px-4 py-3">ID</th>
            <th className="px-4 py-3 text-right">Saldo</th>
            <th className="px-4 py-3 text-right">Gasto/día</th>
            <th className="px-4 py-3 text-right">Días restantes</th>
            <th className="px-4 py-3">Riesgo</th>
            <th className="px-4 py-3">Último consumo</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr
              key={s.usuario_identificacion}
              className="border-b border-bio-100 hover:bg-bio-50 transition-colors"
              data-testid={`at-risk-row-${s.usuario_identificacion}`}
            >
              <td className="px-4 py-3 font-medium text-bio-900 max-w-[18ch] truncate">{s.nombre_estudiante}</td>
              <td className="px-4 py-3 text-bio-500 font-mono text-xs">{s.usuario_identificacion}</td>
              <td className="px-4 py-3 text-right font-mono text-bio-900">{fmt(s.current_balance)}</td>
              <td className="px-4 py-3 text-right font-mono text-bio-500">{fmt(s.avg_daily_spend)}</td>
              <td className="px-4 py-3 text-right font-mono font-semibold text-bio-900">{s.days_remaining}</td>
              <td className="px-4 py-3">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${riskClass[s.risk_level] || "bg-bio-100 text-bio-700"}`}>
                  {s.risk_level.toUpperCase()}
                </span>
              </td>
              <td className="px-4 py-3 text-bio-500 text-xs">{s.last_consumption_date?.slice(0, 10) || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AtRiskTable;
