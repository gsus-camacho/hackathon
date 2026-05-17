# BioAlert+ — Product Requirements Document

## Original Problem Statement
BioAlert+: layer on Biofood(read-only). New DB holds intelligence. Goal: passive sales → decisions/safety/revenue.

DBs:
- **Biofood(R) PostgreSQL**: hackaton_ventas, hackaton_recargas
- **BioAlert+(W) MongoDB**: packages, allergens, ratings, recommendations, bot_sessions

Stack: **Astro + React + Tailwind + API + TS**

Modules (schemas/services/repos/types/errors):
- discounts: dynamic packages + recharges
- notifications: WhatsApp (allergens / balance / daily)
- feedback: ratings
- planifications: balance prediction
- statistics: benchmark + satisfaction
- recommendations: Gemini AI

ConversationHandler (WhatsApp): intent → DB → Gemini
- Intents: consumption / balance / package / alerts

Triggers:
- low balance → package offer
- allergen → parent alert
- no consumption@12PM → alert
- Friday → nutritional report

## Architecture Implemented (2026-05-17)
- **Frontend**: Astro 4 (SSR) + React islands + Tailwind on port 3000
- **Backend**: FastAPI on port 8001 (modular per spec)
- **PostgreSQL**: live read-only access to Biofood (`biofooddb` @ 3.208.123.187)
  - 4.2M ventas + 305K recargas + 10.3K students
- **MongoDB**: BioAlert+ writes (`bioalert_plus`)
- **LLM**: Gemini 3 Flash via Emergent LLM key
- **WhatsApp**: Twilio Sandbox API

## Personas
- **Nutritionist / School Director**: dashboard user, makes decisions on packages, monitors alerts.
- **Parent (Acudiente)**: WhatsApp user via BioBot for balance/consumption/alerts queries.
- **Student**: subject of allergen / balance tracking (passive).

## What's Been Implemented (2026-05-17)
- ✅ Astro frontend with sidebar navigation (Biofood-inspired modernized)
- ✅ Dashboard with real KPIs, area chart (14d series), activity feed, top products
- ✅ `discounts/` module: dynamic packages (Combo Estrella, Rescate Saldo Bajo, Mega Pack)
- ✅ `notifications/` module: Twilio WhatsApp send, outbox, webhook receiver
- ✅ `feedback/` module: 5-star ratings with avg/count summary
- ✅ `planifications/` module: at-risk student list with real balance calculations
- ✅ `statistics/` module: KPIs, daily series, top products, school ranking
- ✅ `recommendations/` module: Gemini-generated AI insights (focus: revenue/nutrition/safety/general)
- ✅ Allergen profiles (under recommendations module) with risk-check endpoint
- ✅ BioBot ConversationHandler: intent detection + Gemini reply + session memory
- ✅ All 6 modules follow strict schemas/services/repositories/types/errors layout
- ✅ SSR cache (45s TTL) to mitigate heavy PostgreSQL aggregations
- ✅ 24/24 backend pytest passing

## Prioritized Backlog

### P0 (production hardening)
- Authentication (Emergent Google Auth or JWT) - currently dashboard is open
- Persistent cache layer (Redis) for heavy aggregations instead of in-memory
- Schedulers (APScheduler) for triggers: `no_consumption@12PM`, `Friday→nutritional report`
- Configure Twilio production webhook URL: `POST /api/notifications/whatsapp/webhook`

### P1 (depth)
- Per-school dashboard view (drill-down from school ranking)
- Cross-school benchmark page with delta vs network average
- Package targeting: auto-send `package_offer` WhatsApp to students_at_risk
- Student detail page (consumption history + balance trend + nutrition profile)
- Excel/CSV export for at-risk list and revenue reports

### P2 (polish)
- Mobile-first redesign of sidebar (currently uses horizontal mobile nav)
- Real-time updates (WebSocket) on Activity Feed
- Multi-language toggle (Spanish base + English)
- Allergen detection by image (Gemini Vision)
- Dark mode for dashboard

## Open Issues / Notes
- PostgreSQL ventas table has all-TEXT columns; backend uses `CAST(... AS NUMERIC/INT)` per spec.
- Some students show negative balance — total consumption exceeds total recharges in dataset; this is reflective of real Biofood hackathon data, not a bug.
- Twilio sandbox: recipients must first send "join <code>" to the sandbox number before receiving outbound messages.

## Next Tasks
1. Wire up scheduler (APScheduler) for daily 12pm no-consumption check + Friday nutrition report.
2. Add per-school filter on dashboard.
3. Auth layer (recommend Emergent Google Auth).
4. Persistent recommendation impact tracking — store outcomes when packages are accepted/declined.
