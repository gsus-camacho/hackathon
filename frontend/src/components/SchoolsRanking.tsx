import React from "react";

interface SchoolItem {
  nit_colegio: string;
  colegio: string;
  total_students: number;
  total_revenue: number;
  total_transactions: number;
  revenue_per_student: number;
}

function formatCOP(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toLocaleString("es-CO")}`;
}

export const SchoolsRanking: React.FC<{ data: SchoolItem[]; days?: number }> = ({
  data,
  days = 90,
}) => {
  if (data.length === 0) {
    return (
      <p className="text-sm text-slate-500 py-6 text-center" data-testid="schools-ranking-empty">
        Sin datos de colegios para el período seleccionado.
      </p>
    );
  }

  const maxRev = Math.max(...data.map((d) => d.total_revenue), 1);

  return (
    <div className="space-y-3" data-testid="schools-ranking">
      {data.slice(0, 8).map((school, i) => {
        const pct = (school.total_revenue / maxRev) * 100;
        return (
          <div key={i} className="group" data-testid={`school-row-${i}`}>
            <div className="flex items-center gap-3">
              <span className="w-6 text-xs font-mono text-slate-400 text-right shrink-0">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-800 truncate">
                    {school.colegio}
                  </span>
                  <span className="text-sm font-mono font-medium text-slate-700 shrink-0 ml-2">
                    {formatCOP(school.total_revenue)}
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-700"
                    style={{ width: `${Math.max(pct, 4)}%` }}
                  />
                </div>
                <div className="flex items-center gap-4 mt-1 text-[11px] text-slate-400">
                  <span>{school.total_students} estudiantes</span>
                  <span>{school.total_transactions.toLocaleString("es-CO")} txns</span>
                  <span>{formatCOP(school.revenue_per_student)}/est.</span>
                </div>
              </div>
            </div>
          </div>
        );
      })}
      <p className="text-xs text-slate-400 font-mono mt-2">
        Revenue por colegio · últimos {days} días
      </p>
    </div>
  );
};

export default SchoolsRanking;
