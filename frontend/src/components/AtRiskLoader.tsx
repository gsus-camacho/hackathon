import React, { useEffect, useState } from "react";
import { Loader2, AlertTriangle } from "lucide-react";
import AtRiskTable from "./AtRiskTable";
import { clientGet } from "../lib/api";

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

export const AtRiskLoader: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [students, setStudents] = useState<Student[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    clientGet(apiBase, "/planifications/at-risk?limit=50")
      .then((d) => alive && setStudents(d))
      .catch((e) => alive && setErr(e?.message || "Error cargando datos"));
    return () => {
      alive = false;
    };
  }, [apiBase]);

  if (err) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-danger" data-testid="at-risk-error">
        <div className="flex items-center gap-2 font-medium">
          <AlertTriangle className="h-4 w-4" /> Error al cargar
        </div>
        <p className="text-sm mt-1">{err}</p>
      </div>
    );
  }

  if (students === null) {
    return (
      <div className="rounded-xl border border-bio-200 bg-white p-12 text-center" data-testid="at-risk-loading">
        <Loader2 className="h-6 w-6 text-bio-500 animate-spin mx-auto mb-3" />
        <p className="text-sm text-bio-500">
          Calculando estudiantes en riesgo… (analizando ventas y recargas)
        </p>
      </div>
    );
  }

  return <AtRiskTable students={students} />;
};

export default AtRiskLoader;
