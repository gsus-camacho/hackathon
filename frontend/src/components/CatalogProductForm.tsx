import React, { useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { clientPost } from "../lib/api";

export const CatalogProductForm: React.FC<{ apiBase: string; defaultNit?: string }> = ({
  apiBase,
  defaultNit = "",
}) => {
  const [productName, setProductName] = useState("");
  const [nit, setNit] = useState(defaultNit);
  const [price, setPrice] = useState(5000);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim() || !nit.trim()) return;
    setBusy(true);
    setResult(null);
    try {
      const res = await clientPost<{ approvals_created: number }>(apiBase, "/approvals/catalog/products", {
        product_name: productName.trim(),
        nit_colegio: nit.trim(),
        unit_price: price,
      });
      setResult(`Producto registrado. ${res.approvals_created} solicitudes de aprobación enviadas por WhatsApp.`);
      setProductName("");
    } catch {
      setResult("No se pudo registrar el producto. Verifica que el backend esté activo.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="rounded-xl border border-bio-200 bg-bio-50/50 p-4 mb-6" data-testid="catalog-product-form">
      <h3 className="font-heading font-semibold text-bio-900 text-sm mb-3">Añadir producto al catálogo</h3>
      <p className="text-xs text-bio-500 mb-4">
        Notifica a los padres por WhatsApp para permitir o bloquear. Sin respuesta en 24h, Gemini decide (Pilar 2).
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <input
          className="rounded-lg border border-bio-200 px-3 py-2 text-sm"
          placeholder="Nombre del producto"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          data-testid="catalog-product-name"
        />
        <input
          className="rounded-lg border border-bio-200 px-3 py-2 text-sm font-mono"
          placeholder="NIT colegio"
          value={nit}
          onChange={(e) => setNit(e.target.value)}
          data-testid="catalog-nit"
        />
        <input
          type="number"
          className="rounded-lg border border-bio-200 px-3 py-2 text-sm"
          value={price}
          onChange={(e) => setPrice(Number(e.target.value))}
          data-testid="catalog-price"
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className="mt-3 inline-flex items-center gap-2 rounded-lg bg-brand text-white px-4 py-2 text-sm font-medium disabled:opacity-50"
        data-testid="catalog-submit"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        Publicar y notificar padres
      </button>
      {result && <p className="text-xs text-bio-600 mt-2">{result}</p>}
    </form>
  );
};

export default CatalogProductForm;
