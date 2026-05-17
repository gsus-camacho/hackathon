import React from "react";

export const WhatsAppFlowMockup: React.FC = () => (
  <div className="mx-auto w-full max-w-[280px]" data-testid="whatsapp-flow-mockup">
    <div className="rounded-[2rem] border-[6px] border-bio-900 bg-bio-900 p-2 shadow-xl">
      <div className="rounded-[1.4rem] overflow-hidden bg-[#ECE5DD] min-h-[420px] flex flex-col">
        <header className="bg-[#075E54] text-white px-4 py-3 flex items-center gap-3">
          <span className="w-9 h-9 rounded-full bg-emerald-400/30 grid place-items-center text-xs font-semibold">BF</span>
          <span>
            <span className="block text-sm font-semibold">Biofood · Cafetería</span>
            <span className="block text-[11px] opacity-80">en línea</span>
          </span>
        </header>
        <div className="flex-1 p-3 space-y-3">
          <Bubble label="PAQUETE MENSUAL">
            Hola María, ¿quieres asegurar las loncheras de Tomás todo octubre?
            <span className="block mt-2 text-[10px] font-mono bg-white/60 px-2 py-0.5 rounded w-fit">Incentivo · +1 snack gratis</span>
            <span className="flex gap-2 mt-2 flex-wrap">
              <Btn kind="primary">Activar paquete</Btn>
              <Btn>Más tarde</Btn>
            </span>
          </Bubble>
          <Bubble label="CONSUMO 12:14 PM">
            Tomás compró <b>Sandwich integral</b>. ¿Cómo le pareció?
            <span className="flex gap-2 mt-2 text-lg">
              <button type="button" aria-label="positivo">👍</button>
              <button type="button" aria-label="negativo">👎</button>
            </span>
          </Bubble>
          <Bubble label="NUEVO PRODUCTO">
            La cafetería añadió <b>Brownie de chocolate</b> al catálogo.
            <span className="flex gap-2 mt-2 flex-wrap">
              <Btn kind="success">Permitir</Btn>
              <Btn kind="danger">Bloquear</Btn>
            </span>
          </Bubble>
        </div>
      </div>
    </div>
    <p className="text-center text-[10px] font-mono text-bio-500 mt-3">Canal: WhatsApp Business API · sin app instalada</p>
  </div>
);

function Bubble({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <article className="bg-white rounded-lg rounded-tl-none p-3 text-[13px] text-bio-900 shadow-sm">
      <p className="text-[9px] font-mono font-semibold text-brand mb-1 tracking-wide">{label}</p>
      {children}
    </article>
  );
}

function Btn({ children, kind }: { children: React.ReactNode; kind?: "primary" | "success" | "danger" }) {
  const map = {
    primary: "bg-brand text-white",
    success: "bg-ok/15 text-ok border border-ok/30",
    danger: "bg-red-50 text-danger border border-red-200",
  } as const;
  const cls = kind ? map[kind] : "bg-bio-100 text-bio-700";
  return <span className={`text-[11px] font-medium px-2.5 py-1 rounded-md ${cls}`}>{children}</span>;
}

export default WhatsAppFlowMockup;
