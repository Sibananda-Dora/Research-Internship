# Slide 7 — Implementation & Coding

> The twin ships as a **FastAPI service + React dashboard**. This slide zooms into the **live Real-Time Monitor** path — how data is fetched, refreshed every 60 s, interpolated between polls, and turned into a prediction.

## Implementation stack (brief)

- **Backend:** FastAPI, ~20 endpoints; `run_orchestrator` → `DAGOrchestrator` (5 model nodes).
- **Models:** PyTorch `LSTMAttention` + XGBoost + Ridge meta-learner (`predict.py`).
- **Frontend:** React 19 + Vite — `RealTimeMonitor`, `OdishaGISMap`, `DSSChat`, `SimulatorPage`.
- **Data:** NASA POWER (history / climatology) + Open-Meteo (live) — both reduced to **4 variables × 12 weeks**.

## Real-Time Monitor — how it actually happens

- **Poll:** frontend → `POST /api/realtime/coordinate` every **60 s** (`POLL_INTERVAL = 60000`).
- **Fetch:** one Open-Meteo call → current snapshot + 16-day forecast.
- **Interpolate:** frontend 1 s ticker linearly blends previous→latest poll (`progress = elapsed/60 s`) → smooth gauges. Backend `realtime_cache` interpolates a fallback if Open-Meteo fails (`is_mocked`).
- **Blend:** 20-yr climatology + `forecast` weeks + `now` at `current_week`; `week_sources[12]` tags each week.
- **Predict:** blended 12-week profile → `run_orchestrator(full_diagnosis)` → yield + failure + triggers.
- **Render:** 4 gauges (Temp/Humidity/Precip/Soil) + live telemetry & prediction streams + triggers; `is_mocked` flags fallback.

```mermaid
flowchart TD
    A["1. Frontend polls every 60 s<br/>POST /api/realtime/coordinate"]
    B["2. Open-Meteo — one call<br/>live snapshot + 16-day forecast"]
    C["3. Backend caches last 2 reads<br/>realtime_cache (fallback if API fails)"]
    D["4. Frontend interpolates every 1 s<br/>smooth glide between 60 s polls"]
    E["5. Blend 12-week profile<br/>climatology + forecast + now<br/>week_sources tags each week"]
    F["6. Orchestrator predicts<br/>yield + failure + triggers"]
    G["7. Dashboard<br/>4 gauges + 12-week bar"]
    A --> B --> C --> D --> E --> F --> G
    G -.->|"next 60 s — refresh cycle repeats"| A
```

**Code anchors:** backend `main.py` — `realtime_cache` (L591) · `/api/realtime/coordinate` (L659) · `_interpolate_snapshot` (L612, linear for T2M/RH2M/GWETROOT, hold-last for PRECTOTCORR) · `_get_climatology` (L593) · `_aggregate_hourly_to_weekly` (L624); frontend `RealTimeMonitor.jsx` — `POLL_INTERVAL = 60000` (L7) · 1-second interpolation ticker `setInterval(tick, 1000)` (L218) · linear blend `t(a,b) = a + (b-a)*progress` (L160).

---

## Reference — External Weather APIs (API Working)

> The detailed algorithm write-ups for NASA POWER (Algorithm A) and Open-Meteo (Algorithm B) — the 4×12 schema, aggregation rules (SUM precip / MEAN temp-humidity-soil), `week_sources` provenance, and the fallback chain — go here. This replaces the old standalone `api-working.md`.
