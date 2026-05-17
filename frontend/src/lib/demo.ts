const sampleKpis = {
  active_alerts: 27,
  allergen_profiles: 64,
  students_at_risk: 14,
  total_revenue_30d: 248_500_000,
  total_recargas_30d: 52_800_000,
  total_students: 1_247,
  bot_sessions_today: 43,
  satisfaction_score: 4.32,
  package_revenue: 28_700_000,
};

const sampleSeries = Array.from({ length: 30 }, (_, index) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - index));
  const weekday = date.getDay();
  const isWeekend = weekday === 0 || weekday === 6;
  const base = isWeekend ? 2_000_000 : 7_500_000;
  const noise = Math.round((Math.random() - 0.5) * 1_500_000);
  return {
    date: date.toISOString().slice(0, 10),
    ventas: base + index * 80_000 + noise,
    recargas: Math.round((base + noise) * 0.22 + index * 15_000),
  };
});

const sampleTopProducts = [
  { name: "Wrap de pollo", units: 520, revenue: 4_420_000 },
  { name: "Jugo natural naranja", units: 430, revenue: 3_120_000 },
  { name: "Arepa de huevo", units: 385, revenue: 2_870_000 },
  { name: "Yogur bebida", units: 340, revenue: 2_300_000 },
  { name: "Snacks de fruta", units: 290, revenue: 2_090_000 },
  { name: "Sandwich integral", units: 260, revenue: 1_980_000 },
  { name: "Bowl saludable", units: 210, revenue: 1_760_000 },
  { name: "Agua saborizada", units: 185, revenue: 1_250_000 },
  { name: "Galleta avena", units: 160, revenue: 960_000 },
  { name: "Empanada de carne", units: 148, revenue: 888_000 },
  { name: "Fruta entera", units: 135, revenue: 675_000 },
  { name: "Brownie de chocolate", units: 120, revenue: 840_000 },
];

const sampleActivity = [
  { timestamp: "2026-05-17T10:24:00", kind: "venta", title: "Paquete semanal activado", detail: "María C. activó Combo Energía Escolar para Sofía" },
  { timestamp: "2026-05-17T09:45:00", kind: "alert", title: "Alerta de alérgeno bloqueada", detail: "Producto con maní bloqueado automáticamente para Mateo P." },
  { timestamp: "2026-05-17T09:30:00", kind: "venta", title: "Consumo registrado", detail: "Tomás R. compró Sandwich integral · COP 8.500" },
  { timestamp: "2026-05-16T18:12:00", kind: "venta", title: "Recarga de saldo", detail: "Acudiente cargó COP 50.000 para Valentina G." },
  { timestamp: "2026-05-16T14:20:00", kind: "alert", title: "Saldo bajo detectado", detail: "Estudiante Lucas M. tiene 1 día de saldo restante" },
  { timestamp: "2026-05-16T08:54:00", kind: "venta", title: "Micro-rating recibido", detail: "👍 para Jugo natural naranja — rating 4.5/5" },
  { timestamp: "2026-05-15T16:30:00", kind: "alert", title: "Nuevo producto analizado", detail: "Gemini verificó Brownie de chocolate contra 12 perfiles" },
  { timestamp: "2026-05-15T11:00:00", kind: "venta", title: "Paquete mensual completado", detail: "Andrés P. alcanzó meta de COP 85.000 — recompensa desbloqueada 🎁" },
];

const sampleSchools = [
  { colegio: "Colegio San José", nit_colegio: "900123456-7", total_students: 248 },
  { colegio: "Institución La Paz", nit_colegio: "900765432-1", total_students: 196 },
  { colegio: "Colegio Lumina", nit_colegio: "900998877-0", total_students: 145 },
  { colegio: "Colegio Nuevo Amanecer", nit_colegio: "900112233-9", total_students: 122 },
  { colegio: "Liceo del Caribe", nit_colegio: "900445566-3", total_students: 198 },
  { colegio: "Colegio Bilingüe del Norte", nit_colegio: "900778899-2", total_students: 167 },
  { colegio: "Instituto Moderno", nit_colegio: "900334455-8", total_students: 171 },
];

const samplePackages = [
  {
    id: "pkg-01",
    name: "Combo Energía Escolar",
    description: "Paquete ideal para estudiantes con actividad física media.",
    items: [
      { product_name: "Wrap de pollo", quantity: 1, unit_price: 8500 },
      { product_name: "Jugo natural naranja", quantity: 1, unit_price: 6500 },
      { product_name: "Snacks de fruta", quantity: 1, unit_price: 5500 },
    ],
    original_total: 26_500,
    discounted_total: 22_500,
    discount_pct: 15,
    target_segment: "general",
    valid_until: "2026-05-31",
    active: true,
  },
  {
    id: "pkg-02",
    name: "Paquete Balance Vital",
    description: "Recomendado para niños con requerimientos bajos en azúcar.",
    items: [
      { product_name: "Arepa de huevo", quantity: 1, unit_price: 7300 },
      { product_name: "Agua saborizada", quantity: 1, unit_price: 3800 },
      { product_name: "Yogur bebida", quantity: 1, unit_price: 5200 },
    ],
    original_total: 16_300,
    discounted_total: 13_900,
    discount_pct: 15,
    target_segment: "low_balance",
    valid_until: "2026-05-28",
    active: true,
  },
  {
    id: "pkg-03",
    name: "Paquete Semanal Completo",
    description: "5 almuerzos + 5 snacks para toda la semana escolar.",
    items: [
      { product_name: "Sandwich integral", quantity: 5, unit_price: 8500 },
      { product_name: "Jugo natural naranja", quantity: 5, unit_price: 6500 },
      { product_name: "Snacks de fruta", quantity: 5, unit_price: 5500 },
    ],
    original_total: 105_000,
    discounted_total: 89_000,
    discount_pct: 15,
    target_segment: "high_consumption",
    valid_until: "2026-06-15",
    active: true,
  },
];

const sampleRecommendations = [
  {
    id: "rec-01",
    title: "Optimizar ofertas de recargas",
    summary: "Los estudiantes con saldo bajo consumen 28% más cuando reciben recordatorios a media mañana.",
    rationale: "Enviar notificaciones de recarga personalizadas aumenta la conversión y reduce interrupciones en compras.",
    kind: "revenue",
    impact_score: 79,
  },
  {
    id: "rec-02",
    title: "Priorizar alertas de alergias",
    summary: "Los perfiles de alérgenos del 12% de la red no están cubiertos por inventario seguro.",
    rationale: "Marcar productos con etiquetas claras y bloquear opciones peligrosas reduce rechazos y reclamos.",
    kind: "safety",
    impact_score: 86,
  },
  {
    id: "rec-03",
    title: "Paquetes para altos consumidores",
    summary: "Un 22% de los estudiantes compra más de 2 horas después de clases.",
    rationale: "Proponer paquetes con descuento en horarios clave mejora ticket promedio sin bajar margen.",
    kind: "operational",
    impact_score: 68,
  },
  {
    id: "rec-04",
    title: "Descontinuar Galleta avena",
    summary: "SI de 0.34 y ventas -14% vs mediana nacional. Producto sin demanda sostenible.",
    rationale: "Liberar espacio de inventario para productos con mayor rotación y satisfacción.",
    kind: "operational",
    impact_score: 72,
  },
];

const sampleAllergens = [
  {
    id: "alg-01",
    usuario_identificacion: "0010066601",
    nombre_estudiante: "Mateo P.",
    identificacion_padre: "0802200072",
    nit_colegio: "900123456-7",
    allergens: ["mani", "lactosa"],
    notes: "Requiere opción sin nuez y sin lácteos cuando esté disponible.",
  },
  {
    id: "alg-02",
    usuario_identificacion: "0010066602",
    nombre_estudiante: "Sofía C.",
    identificacion_padre: "0802200081",
    nit_colegio: "900765432-1",
    allergens: ["gluten"],
    notes: "Prefiere almuerzos vegetarianos por sensibilidad al gluten.",
  },
  {
    id: "alg-03",
    usuario_identificacion: "0010066603",
    nombre_estudiante: "Valentina G.",
    identificacion_padre: "0802200095",
    nit_colegio: "900998877-0",
    allergens: ["huevo", "soya"],
    notes: "Alergia severa a huevo. Verificar siempre composición.",
  },
];

const sampleHijos = [
  {
    id: "hijo-001",
    usuario_identificacion: "0010066601",
    nombre_estudiante: "Mateo P.",
    identificacion_padre: "0802200072",
    nombre_padre: "Andrés P.",
    nit_colegio: "900123456-7",
    colegio: "Colegio San José",
    grado: "5°",
    allergens: ["mani", "lactosa"],
    notes: "Necesita refrigerio temprano y Whatsapp de recordatorio.",
    parent_phone: "+573004280744",
  },
  {
    id: "hijo-002",
    usuario_identificacion: "0010066602",
    nombre_estudiante: "Sofía C.",
    identificacion_padre: "0802200081",
    nombre_padre: "María C.",
    nit_colegio: "900765432-1",
    colegio: "Institución La Paz",
    grado: "4°",
    allergens: ["gluten"],
    notes: "Alergia leve a gluten; evita panes y galletas industriales.",
    parent_phone: "+573002112233",
  },
  {
    id: "hijo-003",
    usuario_identificacion: "0010066603",
    nombre_estudiante: "Valentina G.",
    identificacion_padre: "0802200095",
    nombre_padre: "Carolina G.",
    nit_colegio: "900998877-0",
    colegio: "Colegio Lumina",
    grado: "3°",
    allergens: ["huevo", "soya"],
    notes: "Alergia severa a huevo. Solo productos verificados.",
    parent_phone: "+573005443322",
  },
  {
    id: "hijo-004",
    usuario_identificacion: "0010066604",
    nombre_estudiante: "Tomás R.",
    identificacion_padre: "0802200110",
    nombre_padre: "Ricardo R.",
    nit_colegio: "900123456-7",
    colegio: "Colegio San José",
    grado: "6°",
    allergens: [],
    notes: "Sin restricciones alimentarias. Alto consumidor.",
    parent_phone: "+573006778899",
  },
];

const sampleNotifications = [
  {
    id: "notif-01",
    kind: "allergen_alert",
    recipient_phone: "whatsapp:+573004280744",
    message: "⛔ Intento de compra con maní detectado para Mateo P. Producto bloqueado automáticamente.",
    status: "delivered",
    read: false,
    created_at: "2026-05-17T11:05:00",
  },
  {
    id: "notif-02",
    kind: "low_balance",
    recipient_phone: "whatsapp:+573002112233",
    message: "⚠️ Saldo bajo: Sofía C. tiene COP 1.800 restantes (~0.3 días).",
    status: "delivered",
    read: false,
    created_at: "2026-05-17T09:42:00",
  },
  {
    id: "notif-03",
    kind: "package_offer",
    recipient_phone: "whatsapp:+573004280744",
    message: "📦 Nuevo paquete Balance Vital disponible para tu hijo. 15% de descuento esta semana.",
    status: "sent",
    read: true,
    created_at: "2026-05-16T09:20:00",
  },
  {
    id: "notif-04",
    kind: "consumption",
    recipient_phone: "whatsapp:+573006778899",
    message: "🍽️ Tomás R. compró Sandwich integral (COP 8.500) a las 12:14. ¿Cómo le pareció? 👍👎",
    status: "delivered",
    read: false,
    created_at: "2026-05-17T12:15:00",
  },
  {
    id: "notif-05",
    kind: "new_product",
    recipient_phone: "whatsapp:+573005443322",
    message: "🆕 La cafetería añadió Brownie de chocolate al catálogo. Gemini verificó: compatible con el perfil de Valentina.",
    status: "delivered",
    read: true,
    created_at: "2026-05-16T15:30:00",
  },
  {
    id: "notif-06",
    kind: "reward",
    recipient_phone: "whatsapp:+573004280744",
    message: "🎁 ¡Mateo P. alcanzó la meta semanal! Recompensa desbloqueada: Bebida gratis.",
    status: "delivered",
    read: true,
    created_at: "2026-05-15T16:00:00",
  },
];

const sampleFeedbackProducts = [
  { product_name: "Wrap de pollo", up: 24, down: 3, total: 27, score_pct: 89 },
  { product_name: "Jugo natural naranja", up: 18, down: 2, total: 20, score_pct: 90 },
  { product_name: "Arepa de huevo", up: 12, down: 5, total: 17, score_pct: 71 },
  { product_name: "Sandwich integral", up: 22, down: 1, total: 23, score_pct: 96 },
  { product_name: "Yogur bebida", up: 15, down: 4, total: 19, score_pct: 79 },
  { product_name: "Bowl saludable", up: 10, down: 3, total: 13, score_pct: 77 },
];

const feedbackSummary = { average: 4.32, count: 119 };

function keepTop<T>(items: T[], limit: number) {
  return items.slice(0, limit);
}

function parseLimit(url: URL, defaultLimit: number) {
  const limit = Number(url.searchParams.get("limit"));
  return Number.isFinite(limit) && limit > 0 ? limit : defaultLimit;
}

function parseReadFilter(url: URL) {
  const read = url.searchParams.get("read");
  if (read === "true") return true;
  if (read === "false") return false;
  return undefined;
}

function sampleActivePlanForChild(hijoId: string) {
  return {
    id: `plan-${hijoId}`,
    hijo_id: hijoId,
    week_start: new Date().toISOString().slice(0, 10),
    minimum_budget: 42_000,
    items: [
      { day: 0, product_name: "Wrap de pollo", quantity: 1, unit_price: 8500 },
      { day: 1, product_name: "Jugo natural naranja", quantity: 1, unit_price: 6500 },
      { day: 2, product_name: "Yogur bebida", quantity: 1, unit_price: 5200 },
      { day: 3, product_name: "Sandwich integral", quantity: 1, unit_price: 8500 },
      { day: 4, product_name: "Snacks de fruta", quantity: 1, unit_price: 5500 },
    ],
    current_total: 34_200,
    goal_met: false,
    reward: "Bebida gratis al completar la semana",
  };
}

function makeNewId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function demoFallback(path: string) {
  const url = new URL(path, "http://demo");
  let pathname = url.pathname;
  if (pathname.startsWith("/api")) pathname = pathname.slice(4);

  if (pathname === "/statistics/kpis") return sampleKpis;
  if (pathname === "/statistics/series") return sampleSeries;
  if (pathname === "/statistics/top-products") return keepTop(sampleTopProducts, parseLimit(url, 12));
  if (pathname === "/statistics/activity") return keepTop(sampleActivity, parseLimit(url, 10));
  if (pathname === "/statistics/schools") return keepTop(sampleSchools, parseLimit(url, 10));
  if (pathname === "/discounts/packages") return samplePackages;
  if (pathname === "/recommendations/") return sampleRecommendations;
  if (pathname === "/recommendations/allergens") return sampleAllergens;
  if (pathname === "/hijos/") return sampleHijos;
  if (pathname.startsWith("/planifications/hijos/") && pathname.endsWith("/active-plan")) {
    const parts = pathname.split("/").filter(Boolean);
    const hijoId = parts[2] || "demo";
    return sampleActivePlanForChild(hijoId);
  }
  if (pathname === "/notifications/") {
    const read = parseReadFilter(url);
    return read === undefined ? sampleNotifications : sampleNotifications.filter((item) => item.read === read);
  }
  if (pathname === "/notifications/unread-count") {
    return { count: sampleNotifications.filter((item) => !item.read).length };
  }
  if (pathname === "/planifications/at-risk") {
    return [
      {
        usuario_identificacion: "0010066601",
        nombre_estudiante: "Mateo P.",
        nit_colegio: "900123456-7",
        current_balance: 1800,
        avg_daily_spend: 6500,
        days_remaining: 1,
        risk_level: "Alto",
        last_consumption_date: "2026-05-17",
        last_recharge_date: "2026-05-14",
      },
      {
        usuario_identificacion: "0010066602",
        nombre_estudiante: "Sofía C.",
        nit_colegio: "900765432-1",
        current_balance: 2200,
        avg_daily_spend: 7200,
        days_remaining: 2,
        risk_level: "Medio",
        last_consumption_date: "2026-05-17",
        last_recharge_date: "2026-05-13",
      },
      {
        usuario_identificacion: "0010066604",
        nombre_estudiante: "Tomás R.",
        nit_colegio: "900123456-7",
        current_balance: 4800,
        avg_daily_spend: 9500,
        days_remaining: 2,
        risk_level: "Medio",
        last_consumption_date: "2026-05-17",
        last_recharge_date: "2026-05-12",
      },
    ];
  }
  if (pathname === "/feedback/products") return sampleFeedbackProducts;
  if (pathname === "/feedback/summary") return feedbackSummary;
  if (pathname === "/statistics/b2b") {
    const benchmarkProducts = sampleTopProducts.slice(0, 8).map((p, i) => {
      const medianUnits = sampleTopProducts.reduce((s, x) => s + x.units, 0) / sampleTopProducts.length;
      const delta = Math.round(((p.units - medianUnits) / medianUnits) * 100);
      return { product: p.name, total_units: p.units, total_revenue: p.revenue, schools_selling: 5 + i, avg_unit_price: Math.round(p.revenue / p.units), delta };
    });
    const satisfactionList = sampleFeedbackProducts.map((f) => {
      const si = f.total > 0 ? Math.round((f.up / f.total) * 100) / 100 : 0;
      return { product: f.product_name, si, action: si >= 0.75 ? "Mantener" as const : si >= 0.50 ? "Revisar" as const : "Descontinuar" as const, up: f.up, down: f.down, total_votes: f.total };
    }).sort((a, b) => b.si - a.si);
    const siValues = satisfactionList.filter((s) => s.total_votes > 0).map((s) => s.si);
    const avgSi = siValues.length ? Math.round((siValues.reduce((s, v) => s + v, 0) / siValues.length) * 100) / 100 : 0;
    return {
      benchmark: benchmarkProducts,
      satisfaction: satisfactionList,
      summary: { total_schools: sampleSchools.length, total_records: 184_320, total_students: 1_247, total_products: 12, total_revenue: 21_303_000, avg_si: avgSi, days: 90 },
      schools: sampleSchools.map((s, i) => ({ ...s, total_revenue: 3_200_000 - i * 320_000, total_transactions: 2_400 - i * 180, revenue_per_student: Math.round((3_200_000 - i * 320_000) / s.total_students) })),
    };
  }

  return [];
}

export function demoPostFallback(path: string, body?: any) {
  const url = new URL(path, "http://demo");
  let pathname = url.pathname;
  if (pathname.startsWith("/api")) pathname = pathname.slice(4);

  if (pathname === "/recommendations/generate") return sampleRecommendations;
  if (pathname === "/discounts/packages/generate") return samplePackages;
  if (pathname === "/notifications/send") {
    const id = makeNewId("notif");
    return {
      id,
      kind: body?.kind || "custom",
      recipient_phone: body?.to || "whatsapp:+573000000000",
      message: body?.body || "Mensaje enviado desde BioAlert+",
      status: "sent",
      read: false,
      created_at: new Date().toISOString(),
    };
  }
  if (pathname === "/hijos/") {
    return {
      id: makeNewId("hijo"),
      usuario_identificacion: body?.usuario_identificacion || "0000000000",
      nombre_estudiante: body?.nombre_estudiante || `Estudiante ${body?.usuario_identificacion || "Nuevo"}`,
      identificacion_padre: body?.identificacion_padre || "0000000000",
      nombre_padre: body?.nombre_padre || "Acudiente Demo",
      nit_colegio: body?.nit_colegio || "900000000-0",
      colegio: body?.colegio || "Colegio Demo",
      grado: body?.grado || "5°",
      allergens: body?.allergens || [],
      notes: body?.notes || "Registro creado.",
      parent_phone: body?.parent_phone || "+573000000000",
    };
  }
  if (pathname === "/recommendations/allergens") {
    return {
      id: makeNewId("alg"),
      ...body,
      allergens: body?.allergens || [],
    };
  }
  if (pathname === "/planifications/plans") {
    return {
      id: makeNewId("plan"),
      hijo_id: body?.hijo_id || "demo",
      week_start: body?.week_start || new Date().toISOString().slice(0, 10),
      minimum_budget: body?.minimum_budget || 42_000,
      items: body?.items || [],
      current_total: 0,
      goal_met: false,
      reward: "Recompensa desbloqueada al completar el presupuesto",
    };
  }
  if (pathname.endsWith("/items")) {
    return {
      id: body?.id || makeNewId("plan"),
      hijo_id: body?.hijo_id || "demo",
      week_start: new Date().toISOString().slice(0, 10),
      minimum_budget: 42_000,
      items: [
        { day: body?.day ?? 0, product_name: body?.product_name || "Wrap de pollo", quantity: body?.quantity || 1, unit_price: body?.unit_price || 8500 },
      ],
      current_total: (body?.quantity || 1) * (body?.unit_price || 8500),
      goal_met: false,
      reward: "Bebida gratis al completar la semana",
    };
  }
  if (pathname === "/feedback/ratings") {
    return {
      id: makeNewId("rate"),
      score: body?.score || 5,
      comment: body?.comment || "Muy buen producto.",
      product_name: body?.product_name || "Wrap de pollo",
      source: body?.source || "dashboard",
      created_at: new Date().toISOString(),
    };
  }
  if (pathname === "/notifications/whatsapp/simulate") {
    return { reply: `Respondiendo desde BioBot: recibí tu mensaje "${body?.Body || ""}". Estado de saldo actualizado.` };
  }

  return {};
}

export function demoDeleteFallback(path: string) {
  const url = new URL(path, "http://demo");
  let pathname = url.pathname;
  if (pathname.startsWith("/api")) pathname = pathname.slice(4);

  if (pathname.startsWith("/discounts/packages/")) return {};
  if (pathname.startsWith("/hijos/")) return {};
  if (pathname.includes("/planifications/plans/") && pathname.includes("/items/")) {
    return sampleActivePlanForChild("demo");
  }

  return {};
}
