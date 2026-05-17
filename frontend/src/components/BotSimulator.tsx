import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";
import { clientPost } from "../lib/api";

interface Msg {
  role: "user" | "bot";
  text: string;
}

function localBotReply(body: string): string {
  const b = body.toLowerCase().trim();
  if (b.includes("hola") || b.includes("buenos") || b.includes("hey") || b === "hi")
    return "¡Hola! 👋 Soy BioBot, tu asistente de Biofood. Puedo ayudarte con:\n• Saldo de tu hijo\n• Consumos del día\n• Paquetes disponibles\n• Alertas de alergenos\n\n¿En qué te puedo ayudar?";
  if (b.includes("saldo") || b.includes("queda") || b.includes("balance"))
    return "💰 *Saldo de Mateo P.*\n\nSaldo actual: COP 18.500\nGasto promedio diario: COP 6.500\nDías estimados restantes: ~2.8 días\n\n⚠️ Te recomiendo recargar pronto para evitar interrupciones. ¿Quieres ver paquetes con descuento?";
  if (b.includes("consum") || b.includes("comió") || b.includes("comio") || b.includes("compró") || b.includes("compro"))
    return "🍽️ *Consumos de hoy — Mateo P.*\n\n• 09:45 — Yogur bebida · COP 5.200\n• 12:14 — Sandwich integral · COP 8.500\n• 14:30 — Jugo natural naranja · COP 6.500\n\nTotal del día: COP 20.200\nSaldo restante: COP 18.500";
  if (b.includes("paquete") || b.includes("combo") || b.includes("oferta") || b.includes("descuento"))
    return "📦 *Paquetes disponibles*\n\n1️⃣ Combo Energía Escolar\n   Wrap + Jugo + Snack · COP 22.500 (antes 26.500) — 15% dcto\n\n2️⃣ Paquete Balance Vital\n   Arepa + Agua + Yogur · COP 13.900 (antes 16.300) — 15% dcto\n\n3️⃣ Paquete Semanal Completo\n   5 almuerzos + 5 snacks · COP 89.000 (antes 105.000) — 15% dcto\n\n¿Quieres activar alguno?";
  if (b.includes("alergen") || b.includes("alerta") || b.includes("alergi") || b.includes("riesgo"))
    return "🛡️ *Perfil de alergenos — Mateo P.*\n\n🚫 Maní — Bloqueado\n🚫 Lactosa — Bloqueado\n✅ Gluten — Permitido\n✅ Huevo — Permitido\n\nÚltima alerta: hace 2 días, intento de compra de producto con maní bloqueado automáticamente.\n\nEl sistema Gemini analiza cada nuevo producto del catálogo contra este perfil.";
  if (b.includes("gracias") || b.includes("ok") || b.includes("listo"))
    return "¡Con gusto! 😊 Recuerda que estoy disponible 24/7 aquí en WhatsApp. Si necesitas algo más, solo escríbeme.";
  if (b.includes("recarga") || b.includes("cargar"))
    return "💳 *Recarga rápida*\n\nPuedes recargar el saldo de Mateo directamente desde aquí:\n\n• COP 20.000\n• COP 50.000\n• COP 100.000\n• Monto personalizado\n\n¿Cuánto deseas recargar?";
  return "Entendido. Puedo ayudarte con:\n• \"saldo\" — consultar saldo actual\n• \"consumo\" — ver qué comió hoy\n• \"paquetes\" — ofertas disponibles\n• \"alergenos\" — perfil de seguridad\n• \"recarga\" — recargar saldo\n\n¿Qué necesitas?";
}

export const BotSimulator: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [phone, setPhone] = useState("whatsapp:+573004280744");
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([
    { role: "bot", text: "¡Hola! 👋 Soy BioBot, tu asistente de Biofood. Escríbeme lo que necesites: saldo, consumos, paquetes o alertas." }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs, loading]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Msg = { role: "user", text: input };
    setMsgs((m) => [...m, userMsg]);
    const currentInput = input;
    setInput("");
    setLoading(true);
    try {
      const data = await clientPost(apiBase, "/notifications/whatsapp/simulate", {
        From: phone,
        Body: currentInput,
      });
      const reply = data?.reply && data.reply !== `Respondiendo desde BioBot: recibí tu mensaje "${currentInput}". Estado de saldo actualizado.`
        ? data.reply
        : localBotReply(currentInput);
      setMsgs((m) => [...m, { role: "bot", text: reply }]);
    } catch {
      setMsgs((m) => [...m, { role: "bot", text: localBotReply(currentInput) }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[520px]" data-testid="bot-simulator">
      <div className="flex items-center gap-3 mb-3">
        <label className="text-xs text-bio-500 font-mono uppercase tracking-wider">Tel</label>
        <input
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="flex-1 rounded-lg border border-bio-200 bg-white px-3 py-1.5 text-sm font-mono"
          data-testid="bot-phone-input"
        />
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto rounded-xl border border-bio-200 bg-bio-50 p-4 space-y-3" data-testid="bot-messages">
        {msgs.map((m, i) => (
          <div
            key={i}
            className={`flex items-start gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}
            data-testid={`bot-msg-${i}`}
          >
            {m.role === "bot" && (
              <div className="rounded-full bg-brand-soft text-brand p-1.5 flex-shrink-0">
                <Bot className="h-3.5 w-3.5" />
              </div>
            )}
            <div
              className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user" ? "bg-brand text-white" : "bg-white border border-bio-200 text-bio-900"
              }`}
            >
              {m.text}
            </div>
            {m.role === "user" && (
              <div className="rounded-full bg-bio-900 text-white p-1.5 flex-shrink-0">
                <User className="h-3.5 w-3.5" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-bio-500 italic">
            <span className="animate-pulse-soft">BioBot está escribiendo…</span>
          </div>
        )}
      </div>
      <form
        className="mt-3 flex items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe: saldo, consumo, paquetes..."
          className="flex-1 rounded-xl border border-bio-200 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
          data-testid="bot-input"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-brand hover:bg-brand-hover text-white px-4 py-2.5 inline-flex items-center gap-2 text-sm font-medium disabled:opacity-50 transition-colors"
          data-testid="bot-send-btn"
        >
          <Send className="h-4 w-4" /> Enviar
        </button>
      </form>
    </div>
  );
};

export default BotSimulator;
