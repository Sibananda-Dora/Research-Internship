# AGENTS.md

## Project
Cognitive Digital Twin for Odisha rice yield prediction. 30 districts, 2 seasons (Kharif/Rabi), 2006-2024.
Multi-model ensemble (LSTM + XGBoost + stacking) routed via DAG orchestrator.

## Commands

```powershell
# Frontend
cd frontend; npm install; npm run dev      # Vite dev server on localhost:5173
npm run build; npm run preview             # Production build

# Backend
cd backend; python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Training pipeline (run in order)
python code/phase-2-training/prepare_data.py
python code/phase-2-training/train.py

# Quick smoke test
python -c "import sys; sys.path.insert(0,'code/phase-2-training'); from predict import CDTPredictor; p=CDTPredictor(); print('OK')"
```

## Architecture Wiring

```
frontend/ (Vite+React, localhost:5173)
  src/App.jsx        → calls backend at http://127.0.0.1:8000
  src/components/    → MapCard, MetricsCard, Timeline, Heatmap, DSSChat, OdishaSVGMap
  src/index.css      → dark glassmorphism theme (621 lines, single file)

backend/ (FastAPI, 0.0.0.0:8000)
  main.py            → 6 routes: /, /api/districts, /api/history, /api/telemetry,
                       /api/predict, /api/simulate, /api/ask
  llm_client.py      → Groq (llama-3.3-70b-versatile) for intent parsing + advisory
  .env               → GROQ_API_KEY (required, loaded automatically)
  requirements.txt   → fastapi, uvicorn, pandas, numpy, groq, httpx

code/phase-2-training/
  prepare_data.py    → outputs prepared_data/*.npy + scalers
  train.py           → outputs models/* (lstm_final.pth, xgb_*.json, meta_*.pkl)
  predict.py         → CDTPredictor class (used by orchestrator + backend)
  orchestrator.py    → DAG router, 5 query types → 5 model nodes
  models/            → Saved weights (do not delete)
  prepared_data/     → Preprocessed arrays + scalers (regeneratable)
```

## Critical Rules (agents get these wrong)

1. **Cross-file model consistency**: `LSTMAttention` class exists in BOTH `train.py` and `predict.py`. Changes to one MUST be mirrored in the other, then re-train.

2. **Feature order**: Static features must be `[d_idx, s_hot[0], s_hot[1], yr_offset]` everywhere (prepare_data.py line ~77, predict.py line ~124). XGBoost features must match in order too.

3. **Year encoding**: Use `year - 2006` (absolute offset), NOT `(year - 2006) / (2024 - 2006)` (scaled). The scaled version breaks temporal generalization.

4. **Train/val/test**: 80/10/10 random split. Validation is used for stacking calibration (no test leakage). Don't change to chronological split — models can't extrapolate post-COVID yield regime.

5. **API contract**: Frontend expects exactly these JSON fields: `predicted_yield`, `failure_probability`, `failure_anomaly`, `attention_weights`, `active_triggers`, `confidence_interval`, `monte_carlo_distribution`. Breaking any of these causes silent mock fallback in the UI.

6. **Cold-start districts**: `predict.py` raises `ValueError` for unknown districts — do NOT silently default to Angul.

7. **Rabi window**: Nov 1–Jan 23 (not Jan 1–Mar 25). The old weekly CSV columns use the wrong window — daily telemetry CSVs use the correct one.

8. **Backend telemetry fallback**: If a district/year/season combo has no record, backend generates mock telemetry (lines ~192-197 in main.py). This is intentional for the digital twin use case.

9. **Frontend mock fallback**: If backend is offline, `App.jsx` generates client-side mock predictions (lines ~73-102). This is good for development but masks missing backend features.

## Frontend-Specific Notes

- Uses **React 19**, **Vite 8**, **ESLint 10** (flat config)
- No TypeScript — all `.jsx` files
- No routing library — single-page app with state selectors
- Dependencies: `leaflet`, `react-leaflet` (maps), `recharts` (charts), `lucide-react` (icons)
- Map components: `OdishaSVGMap.jsx` (inline SVG) + `OdishaGISMap.jsx` (Leaflet)
- `DSSChat.jsx` is currently hardcoded mock — does NOT call `/api/ask`. The `/api/ask` endpoint exists in backend but chat component sends no fetch to it.
- CSS is a single `index.css` file (621 lines) — no CSS modules or CSS-in-JS
- Dark theme with CSS custom properties (`:root` vars); glassmorphism cards via `backdrop-filter`
- Dev server proxy to backend is NOT configured in `vite.config.js` — frontend hits `http://127.0.0.1:8000` directly
- The old `web/` directory is stale; the real frontend is `frontend/`

## Backend Quirks

- `sys.path.insert(0, ...)` at line 13 of `main.py` adds `code/phase-2-training/` — this means the orchestrator and predict modules must be importable from there
- `.env` is loaded in `llm_client.py` (not main.py) — `GROQ_API_KEY` must live in `backend/.env`
- `llm_client.py` uses Groq's `llama-3.3-70b-versatile` — model name is a single string constant at the top of the file
- CORS is wide open (`allow_origins=["*"]`) — fine for dev, change for production

## Current Performance

| Model | Yield R² | Failure AUC |
|---|---|---|
| LSTM (84-step, 56K params) | 0.636 | 0.782 |
| XGBoost (23 features) | 0.736 | 0.801 |
| Stacking (val-calibrated) | **0.736** | **0.814** |

## Data Stats

- `final_dataset.csv`: 1,083 rows, 30 districts, 2006-2024, 0 interpolated rows
- Telemetry: 30 daily CSVs, 16,587 rows each (1981-2026 NASA POWER)
- Rabi (Nov-Jan) has fewer rows (some districts don't cultivate Rabi rice)
- Yield range: 0.0-39.1 Q/Acre; failure rate ~25%
- Post-2020 yield mean doubled (7.8→14.0) — model doesn't extrapolate to this regime
