import React from "react";

interface SatisfactionItem {
  product: string;
  si: number;
  action: "Mantener" | "Revisar" | "Descontinuar";
}

const chipClass: Record<string, string> = {
  Mantener: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Revisar: "bg-amber-50 text-amber-700 border-amber-200",
  Descontinuar: "bg-red-50 text-red-700 border-red-200",
};

export const SatisfactionTable: React.FC<{ data: SatisfactionItem[] }> = ({ data }) => {
  return (
    <div className="overflow-x-auto" data-testid="satisfaction-table">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono border-b border-slate-200">
            <th className="px-4 py-3">Producto</th>
            <th className="px-4 py-3">SI</th>
            <th className="px-4 py-3">Acción</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition-colors" data-testid={`si-row-${i}`}>
              <td className="px-4 py-3 font-medium text-slate-900">{item.product}</td>
              <td className="px-4 py-3 font-mono font-medium text-slate-900">{item.si.toFixed(2)}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${chipClass[item.action] || ""}`}>
                  {item.action}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-slate-400 font-mono mt-3 px-4">SI = frecuencia + repetición + rating WhatsApp · pesos calibrados por cohorte</p>
    </div>
  );
};

export default SatisfactionTable;
