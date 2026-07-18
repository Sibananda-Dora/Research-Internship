# UML Diagrams — Cognitive Digital Twin (Updated v4)

> **Updated from `presentation-2/UML_Diagrams_Detailed.md` (v3).** The v3 diagrams contained *planned/aspirational* elements that do not match the built system — notably a **MQTT message broker** + **VirtualSensor** publisher, and a **Govt API** sync that was never implemented. This v4 revision aligns every diagram with the **actual implementation** verified in the codebase:
> - Historical weather comes from **NASA POWER** (`fetch_nasa_power_telemetry`, Algorithm A); live weather comes from **Open-Meteo** (`/api/realtime/coordinate`, Algorithm B) — both reduced to the same **4 variables × 12 weeks** schema. No MQTT / VirtualSensor is used (historical replay reads the 30 daily CSVs directly; AGENTS.md rule #11: "No MQTT").
> - District selection resolves a pinned coordinate via **boundary point-in-polygon** (`find_district_by_boundary` over `odisha_districts.geojson`); outside the state → `"Unknown"` (no silent default).
> - Live interpolation uses **`realtime_cache`** (t0/v0, t1/v1) between 60 s polls; `week_sources[12]` tags each week `climatology` / `forecast` / `now`.
> - Backend = **FastAPI, ~20 endpoints** + WebSocket `/ws/farm-stream`; orchestrator routes **5 query types → 5 model nodes**.
> - Measured metrics (not the old AGENTS.md figures) are used in examples.

---

## 1. Use Case Diagram (v4)

```mermaid
flowchart LR
    %% Actors
    A(("Agricultural Analyst\n(Primary User)"))
    F(("Farmer\n(End User)"))
    NASA(("NASA POWER API\n«External System»\nhistorical/climatology"))
    OM(("Open-Meteo API\n«External System»\nlive current + 16-day"))

    %% System Boundary
    subgraph CDT ["Cognitive Digital Twin System"]
        direction TB
        UC1(["View District Yield Trends\n(History)"])
        UC2(["Select District on Map\n(boundary point-in-polygon)"])
        UC3(["Get Yield Forecast\n(XGBoost)"])
        UC4(["Get Failure Risk\n(XGBoost + Triggers)"])
        UC5(["Run What-If Simulation\n(MC Dropout)"])
        UC6(["Query Advisory LLM\n(Groq Chat)"])
        UC7(["Monitor Real-Time Twin\n(Open-Meteo + interpolation)"])
        UC8(["Replay Historical Season\n(WebSocket farm-stream)"])
        UC9(["Receive Alert on\nThreshold Breach"])
    end

    %% Analyst interactions
    A --- UC1
    A --- UC2
    A --- UC3
    A --- UC4
    A --- UC5
    A --- UC6
    A --- UC7
    A --- UC8

    %% Farmer interactions (simpler)
    F --- UC3
    F --- UC6
    F --- UC9

    %% External system interactions
    NASA --- UC7
    OM --- UC7
    NASA --- UC8
    UC3 -. "«include»" .-> UC7
    UC4 -. "«include»" .-> UC7
    UC5 -. "«extend»" .-> UC4
```

**Use Case Descriptions**

| UC ID | Name | Primary Actor | Trigger | Result |
|-------|------|--------------|---------|--------|
| UC-01 | View District Yield Trends | Analyst | Select district + season | Historical yield chart with Q1 overlay |
| UC-02 | Select District on Map | Analyst | Click map → point-in-polygon resolve | District name (or "Unknown" if outside Odisha) |
| UC-03 | Get Yield Forecast | Analyst / Farmer | Click district on map | Predicted yield (Q/Acre) |
| UC-04 | Get Failure Risk | Analyst | Request risk assessment | Failure probability + biophysical triggers |
| UC-05 | Run What-If Simulation | Analyst | Adjust climate sliders | Counterfactual yield + risk comparison |
| UC-06 | Query Advisory LLM | Analyst / Farmer | Type natural-language question | Expert advisory (Groq) |
| UC-07 | Monitor Real-Time Twin | Analyst | Open Real-Time Monitor | Live telemetry + prediction (60 s poll, interpolated) |
| UC-08 | Replay Historical Season | Analyst | Start stream (district/year/season/speed) | Replay from 30 daily CSVs via WebSocket |
| UC-09 | Receive Alert | Farmer | Failure probability > threshold | In-app / chat notification |

---

## 2. Class Diagram (v4)

```mermaid
classDiagram
    %% ===== Domain =====
    class District {
        -name: String
        -latitude: Float
        -longitude: Float
        -boundaryPolygon: GeoJSON
    }
    class TelemetryRecord {
        -date: String
        -T2M: Float
        -PRECTOTCORR: Float
        -RH2M: Float
        -GWETROOT: Float
    }
    class FarmState {
        -district: String
        -realtimeCache: Dict
        -weeklyProfile: List~Float~
        -weekSources: List~String~
        +interpolate(t): Dict
    }

    %% ===== ML Core (genuine ensemble) =====
    class LSTMAttention {
        -hidden_dim: Int
        -n_layers: Int
        -district_embedding: Embedding
        -attention: Sequential
        +forward(seq, static): Tuple
    }
    class XGBoostModel {
        -n_estimators: Int
        -max_depth: Int
        +predict_yield(features): Float
        +predict_fail(features): Float
    }
    class MetaLearner {
        -weights: List~Float~
        +predict(base_preds): Float
    }
    class BiophysicalTriggers {
        +evaluate(weekly_12x4): List~String~
    }
    class CDTPredictor {
        -lstm: LSTMAttention
        -xgb: XGBoostModel
        -meta_yield: MetaLearner
        -meta_fail: MetaLearner
        +predict(weather_48, district, season, year): Dict
        +monte_carlo(weather_48, district, season, year, n): Dict
    }

    %% ===== Orchestration =====
    class GraphState {
        +district: String
        +season: String
        +year: Int
        +weather_48: ndarray
        +query_type: Enum
        +xgb_yield: Float
        +lstm_yield: Float
        +mc_ci: Dict
        +triggers: List
        +response: Dict
    }
    class DAGOrchestrator {
        -predictor: CDTPredictor
        +run(district, season, year, weather_48, query_type): Dict
        -node_xgb(state): void
        -node_lstm(state): void
        -node_mc_dropout(state): void
        -node_triggers(state): void
    }

    %% ===== Data clients & serving =====
    class NASAAPIClient {
        +fetch_daily(lat, lon, year, season): Dict
    }
    class OpenMeteoClient {
        +fetch_realtime(lat, lon, season): Dict
    }
    class DistrictResolver {
        -geojson: GeoJSON
        +resolve(lat, lon): String
    }
    class FastAPIBackend {
        +getPredict(district, year, season): Dict
        +postRealtimeCoordinate(): Dict
        +postSimulate(): Dict
        +wsFarmStream(): void
        +getDistricts(): List
    }
    class ReactDashboard {
        +renderPredictions(): void
        +pollRealtime60s(): void
    }

    %% ===== Associations =====
    District "1" --> "1" FarmState : twin state
    FarmState ..> OpenMeteoClient : live-fed

    CDTPredictor *-- LSTMAttention
    CDTPredictor *-- XGBoostModel
    CDTPredictor *-- "2" MetaLearner
    CDTPredictor ..> BiophysicalTriggers : uses
    DAGOrchestrator *-- GraphState
    DAGOrchestrator ..> CDTPredictor : uses

    FastAPIBackend ..> DAGOrchestrator : invokes
    FastAPIBackend ..> DistrictResolver : resolves
    FastAPIBackend ..> NASAAPIClient : historical
    FastAPIBackend ..> OpenMeteoClient : live
    ReactDashboard ..> FastAPIBackend : fetches

    NASAAPIClient ..> TelemetryRecord : produces
    OpenMeteoClient ..> TelemetryRecord : produces
    CDTPredictor ..> TelemetryRecord : consumes as weather_48
    FarmState ..> TelemetryRecord : aggregates to weekly
```

---

## 3. Sequence Diagram — Predict Crop Failure via DAG (v4)

**Flow:** Analyst clicks a district → Frontend calls API → DAG routes to model nodes → Compiled (stacked) response → Dashboard renders. Shows the `FULL_DIAGNOSIS` route (all 5 nodes). For a coordinate pin, `DistrictResolver` runs first.

```mermaid
sequenceDiagram
    actor U as Agricultural Analyst
    participant UI as React Dashboard
    participant API as FastAPI Backend
    participant DAG as DAGOrchestrator
    participant XGB as XGBoost (reg + clf)
    participant LSTM as LSTMAttention
    participant MC as MC Dropout
    participant TRG as Biophysical Triggers
    participant PRED as CDTPredictor

    activate U
    U->>UI: Click district "Ganjam" on map
    activate UI
    UI->>API: GET /api/predict/Ganjam/Kharif/2024
    Note over UI,API: For a coordinate pin, DistrictResolver resolves lat/lon → district first

    activate API
    API->>API: get_telemetry → telemetry_to_flat48 (4 vars × 12 wks = 48)
    API->>DAG: run("Ganjam","Kharif",2024,w48,FULL_DIAGNOSIS)
    
    activate DAG
    Note over DAG: Route = 5 model nodes (FULL_DIAGNOSIS)

    DAG->>XGB: node_xgb_yield + node_xgb_failure
    activate XGB
    XGB->>PRED: predict on scaled features
    activate PRED
    PRED-->>XGB: predictions
    deactivate PRED
    XGB-->>DAG: xgb_yield = 9.4, xgb_fail_prob = 0.18
    deactivate XGB

    DAG->>LSTM: node_lstm_attention
    activate LSTM
    LSTM->>PRED: dnn(seq, static)
    activate PRED
    PRED-->>LSTM: outputs
    deactivate PRED
    LSTM-->>DAG: lstm_yield, lstm_fail_prob, attention_weights
    deactivate LSTM

    DAG->>MC: node_mc_dropout
    activate MC
    MC->>PRED: monte_carlo(500 samples, dropout ON)
    activate PRED
    PRED-->>MC: distribution
    deactivate PRED
    MC-->>DAG: yield CI + std
    deactivate MC

    DAG->>TRG: node_triggers
    activate TRG
    TRG-->>DAG: active_triggers = [] (none fired)
    deactivate TRG

    DAG->>DAG: _compile_response (stacked ensemble)
    Note over DAG: Yield = 0.2·LSTM + 0.8·XGBoost<br/>Fail = 0.68·LSTM + 0.32·XGBoost
    DAG-->>API: compiled result
    deactivate DAG
    
    API-->>UI: {predicted_yield, failure_probability, active_triggers, attention_weights, confidence_interval}
    deactivate API

    UI-->>U: Show yield = 9.4 Q/A, failure = 18%, triggers = none
    deactivate UI
    deactivate U
```

---

## 4. Sequence Diagram — Real-Time Monitor via Open-Meteo (v4, bonus)

**Flow:** Frontend opens Real-Time Monitor → polls `/api/realtime/coordinate` every 60 s → Open-Meteo single call → `realtime_cache` interpolation → climatology base overlaid with forecast/`now` (`week_sources`) → orchestrator `full_diagnosis` → live prediction.

```mermaid
sequenceDiagram
    actor U as Analyst
    participant UI as RealTimeMonitor
    participant API as FastAPI Backend
    participant RES as DistrictResolver
    participant OM as Open-Meteo
    participant CACHE as realtime_cache
    participant DAG as DAGOrchestrator

    activate U
    U->>+UI: Open monitor (lat/lon, district, season)
    UI->>+API: POST /api/realtime/coordinate

    API->>+RES: resolve(lat, lon)
    RES-->>-API: "Ganjam"
    
    API->>+OM: fetch_realtime (single 16-day hourly call)
    OM-->>-API: current snapshot + forecast
    
    API->>API: aggregate → 12-week profile + 20-yr climatology base (week_sources)
    
    API->>+CACHE: store t0/v0, t1/v1 (for 60 s interpolation)
    CACHE-->>-API: stored
    
    API->>+DAG: run("Ganjam", season, year, weekly_48, FULL_DIAGNOSIS)
    DAG-->>-API: prediction
    
    API-->>-UI: {telemetry_weekly, week_sources[12], current_week, prediction, is_mocked}

    UI->>UI: Render 4 gauges + 12-week bar (climatology / forecast / now)
    loop every 60 s (interpolate from CACHE between polls)
        UI->>+API: POST /api/realtime/coordinate (next poll)
        API-->>-UI: updated prediction
    end
    UI-->>-U: Show updated real-time monitor
    deactivate U
```

---

## 5. Architecture Diagram (v4 — 4-Layer, no MQTT)

```mermaid
graph TB
    subgraph L1["Layer 1: Physical Entity"]
        A("30 Odisha Districts")
        B("Farmers & Agronomy")
        C("Climate System")
    end

    subgraph L2["Layer 2: Data Acquisition & Harmonization"]
        D("Govt Yield CSVs\nUPAg 1997-2025") --> F("Data Harmonization\n(prepare_data.py)")
        E("NASA POWER API\n(historical/climatology)") --> F
        F --> G("final_dataset.csv\n1,113 rows, 58 cols")
        G --> H("Telemetry CSVs\n30 x 16,587 daily rows")
        H --> REPLAY("Historical Replay\n(reads daily CSV, no MQTT)")
    end

    subgraph L3["Layer 3: Cognitive Analytics"]
        G --> PREP("prepare_data.py\nfeature engineering")
        PREP --> TRAIN("train.py\nLSTM + XGBoost + Stacking")

        TRAIN --> LSTM("LSTMAttention\n84-step, attention")
        TRAIN --> XGB("XGBoost\n23 features, 500 trees")
        TRAIN --> META("Ridge Meta-Learner\n[0.2L/0.8X yield]\n[0.68L/0.32X fail]")

        LSTM --> DAG("DAG Orchestrator\n5 query types")
        XGB --> DAG
        META --> DAG
        DAG --> TRG("Biophysical Triggers\nDrought/Heat/Flood/Pest")
    end

    subgraph L4["Layer 4: Application & Orchestration"]
        OM("Open-Meteo API\nlive current + 16-day") --> RT("Real-Time Path\nrealtime_cache + week_sources")
        RT --> DAG
        REPLAY --> WS("WebSocket /ws/farm-stream")

        DAG --> API("FastAPI Backend\n~20 endpoints")
        API --> LLM("Groq LLM\nllama-3.3-70b")
        API --> WS2("WebSocket\n/ws/farm-stream")
        WS2 --> UI("React 19 + Vite")
        LLM --> UI
        API --> UI

        UI --> MAP("OdishaGISMap\n(Leaflet, boundary PIP)")
        UI --> TWIN("RealTimeMonitor\ngauges + 12-week bar")
        UI --> CHAT("DSSChat\n(advisory LLM)")
        UI --> FBL("SimulatorPage\n(what-if)")
        UI --> MET("Metrics Cards")
    end

    L1 -. "NASA satellite telemetry" .-> L2
    L4 -. "Advisories & What-If" .-> L1
```

---

## 6. What changed vs presentation-2 (v3)

| Element | v3 (presentation-2) | v4 (this file, actual build) |
|---|---|---|
| Live data transport | MQTT **Message Broker** + **VirtualSensor** publisher | **Open-Meteo** API + `realtime_cache` interpolation (no MQTT; AGENTS rule #11) |
| Historical replay | VirtualSensor → broker → subscriber | Reads 30 daily CSVs directly → WebSocket `/ws/farm-stream` |
| External systems | NASA POWER + (Govt API planned, not built) | NASA POWER (historical) + **Open-Meteo** (live); both → 4×12 schema |
| District selection | Map click (implicit) | Map click → **boundary point-in-polygon** (`DistrictResolver`); outside → "Unknown" |
| Backend | "17 endpoints" | **~20 endpoints** (incl. `/api/realtime/coordinate`, `/api/predict/coordinate`, stream control) |
| LSTM params | `max_depth` implied 6 | `max_depth 4` (actual `train.py`); embedding 30→8, dropout 0.2 |
| XGBoost | standalone | XGBoost + **Ridge stacking meta-learner** (weights 0.2/0.8, 0.68/0.32) |
| Metrics in examples | AGENTS.md (0.736/0.814) | **Measured** (R² 0.712, RMSE 3.63, AUC 0.721, F1 0.455@0.5) |
