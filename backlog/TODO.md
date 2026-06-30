# Backlog — Discussed But Not Yet Implemented

## Priority 1: Government Data Check & Update Pipeline

### Motivation
Supervisor wants to show the digital twin constantly updating with new data. A button checks a government data source, downloads new yield data, fetches telemetry, retrains models, and hot-reloads the backend.

### Backend — New Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/pipeline/check` | POST | Hit `DATA_SOURCE_URL` (from `.env`), compare latest year/season with `final_dataset.csv`. Return `{new_data: bool, latest_year, new_records}` |
| `/api/pipeline/update` | POST | Download new data, launch pipeline in background thread, return `task_id` |
| `/api/pipeline/status/{task_id}` | GET | Return `{status, step, progress, current_step, metrics?}` for frontend polling |
| `/api/pipeline/version` | GET | Return `{current_version, last_trained, model_metrics}` for badge display |

### `.env` addition
```env
DATA_SOURCE_URL=https://data.odisha.gov.in/api/...  # real govt endpoint
# For demo:
DATA_SOURCE_URL=http://localhost:8000/demo-new-data
```

### Pipeline Script: `code/phase-2-training/update_pipeline.py`
```python
# Orchestrates full flow:
# 1. Validate incoming CSV (must have District, Year, Season, Yield_Q_Acre)
# 2. Fetch missing NASA telemetry for those rows
# 3. Append to final_dataset.csv, recalc Q1/Failure_Anomaly
# 4. Backup models/ → models/backup_YYYYMMDD_HHMMSS/
# 5. Run prepare_data.py
# 6. Run train.py
# 7. Write version.json with new metrics
# 8. Signal backend to hot-reload CDTPredictor
```

### Frontend — Pipeline Button & Status Modal

- **Badge in header**: `Model v2.3 | 📡 Check` 
- **Click** → calls `POST /api/pipeline/check`
- **If new data**: confirmation modal: "30 new records for 2025 found. Download and retrain?"
- **On confirm**: calls `POST /api/pipeline/update`, polls `GET /api/pipeline/status/{task_id}` every 2s
- **Animated progress steps**: `🟡 Checking → 🔵 Fetching telemetry → 🔵 Merging → 🔵 Retraining (~120s) → 🟢 Models updated!`
- **Auto-refresh**: Dashboard calls prediction after completion, badge updates to `Model v2.4 | ✅ Updated 2 min ago`

### Demo Data

- Create `sources/data/new_yield_2025_demo.csv` — 30 synthetic rows, one per district, for "2025 Kharif"
- Include a tiny FastAPI route `/demo-new-data` that serves this CSV for the demo flow

---

## Priority 2: Role-Based View Switcher (Farmer / Analyst)

### Motivation
The current dashboard has one view for everyone. Farmers need a simplified interface; analysts need the full data.

### App.jsx — New State
```js
const [userRole, setUserRole] = useState('analyst'); // 'farmer' | 'analyst'
```

### Farmer Mode
- **Hero card**: giant yield number + traffic-light status (🟢/🟡/🔴) with plain language
- **Advisory**: "Your paddy at Kandhamal is at risk — drought detected. Consider irrigating."
- **Simplified map**: big satellite view, coordinate pinning only, no analysis toggles
- **No sim sliders**: replace with 3 preset buttons: "Less Rain", "More Rain", "Heat Wave"
- **No heatmap/timeline clutter** — just map + verdict + advisory
- **Mobile-first layout**: single column, large fonts, high contrast
- **Language toggle**: English / Odia (need translation map for labels)

### Analyst Mode
- Current full dashboard (refined)
- Model comparison panel (LSTM vs XGB vs Ensemble)
- CSV export button for prediction data
- District comparison picker (select 2+ districts to overlay)
- Full What-If simulation sliders with real-time MC distribution histogram
- Raw API trace viewer

### Implementation approach
- Single SPA with a toggle at top-right: `👨‍🌾 Farmer` | `📊 Analyst`
- CSS media queries + conditional rendering per role
- Farmer view is a separate component tree (`FarmerDashboard.jsx`) to keep things clean
- Analyst view is essentially the current `App.jsx` content refactored into `AnalystDashboard.jsx`

---

## Priority 3: Architecture Visualization Overlay

### Motivation
Supervisor wants to show the 4-layer architecture (Physical → Data → Cognitive → Application) working live during a demo.

### Frontend Component: `ArchitectureFlow.jsx`

- 4 horizontal bands, each showing live data
- Glowing dot animates through layers when a prediction runs
- Toggle button (🔬) in the header to show/hide
- Layer data:

| Layer | Live content |
|-------|--------------|
| L1: Physical | `{district}, {season} {year} — {lat}°N, {lng}°E` |
| L2: Data | `final_dataset.csv (1083 rows) → NASA POWER (1981-2026)` |
| L3: Cognitive | `LSTM(56K) + XGB(500 trees) + Stacking [0.2L/0.8X]` |
| L4: Orchestration | `Query: full_diagnosis → Nodes: 5/5 executed → Response sent` |

### Backend — Add `_trace` to prediction responses
```json
"_trace": {
  "layer1_physical": {"district": "Kandhamal", "season": "Kharif", "year": 2024},
  "layer2_data": {"dataset_rows": 1083, "telemetry_source": "NASA POWER 1981-2026"},
  "layer3_cognitive": {"models": ["lstm", "xgb_reg", "xgb_clf", "stacking"], "weights": "0.2L/0.8X"},
  "layer4_orchestration": {"query_type": "full_diagnosis", "nodes_executed": 5}
}
```

---

## Priority 4: Feedback Loop Demo Button

### Motivation
After getting a prediction + advisory, demo the "farmer acts → conditions change → prediction updates" loop.

### Implementation
- New button on prediction cards: **"🧑‍🌾 Simulate Farmer Action"**
- If advisory says "irrigate" → clicking adds +0.15 soil moisture
- If advisory says "drought" → clicking adds +20% precipitation
- Re-runs prediction with modified telemetry
- Shows side-by-side comparison: *Before: 6.7 Q/Acre → After: 7.9 Q/Acre*
- Visual animation: arrow from advisory card → farmer icon → weather change → new prediction

---

## Priority 5: Remaining Small Improvements

### OdishaSVGMap.jsx deprecation
- File still exists in `frontend/src/components/`
- Not imported anywhere after MapCard cleanup
- Can delete once confirmed no regressions

### Mobile breakpoints in CSS
- `index.css` has some `@media` queries but not comprehensive
- Farmer mode needs mobile-first layout
- Specific: `.dashboard-grid` should stack at 768px, `.metrics-row` should show 2 columns at 480px

### Unified error handling
- Backend predictions have no standardized error response shape
- Frontend catch blocks each generate ad-hoc fallback data
- Should create a shared error boundary + fallback format

### Missing frontend env config
- `API_BASE_URL` hardcoded to `http://127.0.0.1:8000` in App.jsx and DSSChat.jsx
- Should move to `VITE_API_BASE_URL` in `.env` file
- Same for Google Maps / Mapbox key if added later
