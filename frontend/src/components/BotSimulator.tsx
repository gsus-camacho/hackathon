import React, { useState } from "react";
import { Send, Bot, User } from "lucide-react";

interface Msg {
  role: "user" | "bot";
  text: string;
  ts?: string;
  intent?: string;
}

export const BotSimulator: React.FC<{ apiBase: string }> = ({ apiBase }) => {
  const [phone, setPhone] = useState("whatsapp:+573004280744");
  const [input, setInput] = useState("Hola, ¿cuál es el saldo de mi hijo?");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Msg = { role: "user", text: input };
    setMsgs((m) => [...m, userMsg]);
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/notifications/whatsapp/simulate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ From: phone, Body: input }),
      });
      const data = await res.json();
      setMsgs((m) => [...m, { role: "bot", text: data.reply || "(sin respuesta)" }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "bot", text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-[640px]" data-testid="bot-simulator">
      <div className="flex items-center gap-3 mb-3">
        <label className="text-xs text-bio-500 font-mono uppercase tracking-wider">Teléfono</label>
        <input
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="flex-1 rounded-lg border border-bio-200 bg-white px-3 py-1.5 text-sm font-mono"
          data-testid="bot-phone-input"
        />
      </div>
      <div className="flex-1 overflow-y-auto rounded-xl border border-bio-200 bg-bio-50 p-4 space-y-3" data-testid="bot-messages">
        {msgs.length === 0 && (
          <div className="text-sm text-bio-500 text-center mt-12">
            Envía un mensaje para probar el ConversationHandler.
            <div className="mt-3 text-xs font-mono">
              Prueba: "saldo", "consumo", "paquetes", "alergenos"
            </div>
          </div>
        )}
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
              className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap ${
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
          <div className="text-xs text-bio-500 italic">BioBot está escribiendo…</div>
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
          placeholder="Escribe un mensaje como padre…"
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
