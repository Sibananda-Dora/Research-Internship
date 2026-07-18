# UML Diagrams — Cognitive Digital Twin (Presentation 2)

Detailed UML diagrams reflecting the actual implementation, mapped to `Format_for slide_presentation_2.docx` slides 3–5.

---

## Table of Contents

1. [Updated Use Case Diagram (v2)](#1-use-case-diagram-v2)
2. [Updated Class Diagram (v3)](#2-class-diagram-v3)
3. [Sequence Diagram: Predict Crop Failure via DAG](#3-sequence-diagram-predict-crop-failure)
4. [Architecture Diagram (v2)](#4-architecture-diagram-v2--4-layer)
5. [State Diagram: FarmState Lifecycle](#5-state-diagram-farmstate-lifecycle)
6. [Appendix: Comparison to PPT-1](#appendix-comparison-to-presentation-1-diagrams)

---

## 1. Use Case Diagram (v2)

**Changes from v1 (Presentation 1):**
- Added `Monitor Real-Time Telemetry Stream` (live telemetry feed)
- Added `Toggle Virtual Sensor` (start/pause/stop replay)
- Added `Receive Alerts` (notifications on threshold breach)
- Split `Check Crop Failure Risk` into `Get Yield Forecast` + `Get Failure Risk` (maps to DAG query types)
- Removed `Sync Seasonal Yield Data` (Govt API integration not implemented)
- Actor `Researcher` renamed to `Agricultural Analyst`

```mermaid
flowchart LR
    %% Actors
    A(("Agricultural Analyst\n(Primary User)"))
    F(("Farmer\n(End User)"))
    NASA(("NASA POWER API\n«External System»"))
    BROKER(("Message Broker\n«Virtual Infrastructure»"))

    %% System Boundary
    subgraph CDT ["Cognitive Digital Twin System"]
        direction TB
        UC1(["View District Yield Trends\n(History)"])
        UC2(["Get Yield Forecast\n(XGBoost)"])
        UC3(["Get Failure Risk\n(XGBoost + Triggers)"])
        UC4(["Run What-If Simulation\n(MC Dropout)"])
        UC5(["Query Advisory LLM\n(Groq Chat)"])
        UC6(["Monitor Real-Time\nTelemetry Stream ✅ NEW"])
        UC7(["Toggle Virtual Sensor\n(Start/Pause/Stop) ✅ NEW"])
        UC8(["View Live Twin Dashboard\n(WebSocket Push) ✅ NEW"])
        UC9(["Receive Alert on\nThreshold Breach ✅ NEW"])
    end

    %% Analyst interactions
    A --- UC1
    A --- UC2
    A --- UC3
    A --- UC4
    A --- UC5
    A --- UC6
    A --- UC8

    %% Farmer interactions (simpler)
    F --- UC2
    F --- UC5
    F --- UC9

    %% External system interactions
    NASA --- UC6
    BROKER --- UC6
    BROKER --- UC7

    %% System dependencies
    UC2 -. "«include»" .-> UC6
    UC3 -. "«include»" .-> UC6
    UC4 -. "«extend»" .-> UC3
    UC8 -. "«include»" .-> UC7
```

**Use Case Descriptions:**

| UC ID | Name | Primary Actor | Trigger | Result |
|-------|------|--------------|---------|--------|
| UC-01 | View District Yield Trends | Analyst | User selects district + season | Historical yield chart |
| UC-02 | Get Yield Forecast | Analyst / Farmer | User clicks district on map | Predicted yield (Q/Acre) |
| UC-03 | Get Failure Risk | Analyst | User requests risk assessment | Failure probability + triggers |
| UC-04 | Run What-If Simulation | Analyst | User adjusts climate sliders | Counterfactual yield comparison |
| UC-05 | Query Advisory LLM | Analyst / Farmer | User types natural language question | Expert advisory response |
| UC-06 | Monitor Real-Time Telemetry | Analyst | Virtual sensor publishes telemetry | Live telemetry feeds into state |
| UC-07 | Toggle Virtual Sensor | Analyst | User clicks Start/Pause/Stop | Stream state changes |
| UC-08 | View Live Twin Dashboard | Analyst | WebSocket push from backend | Real-time yield + telemetry update |
| UC-09 | Receive Alert | Farmer | Failure probability > threshold | Notification (in-app/Telegram) |

---

## 2. Class Diagram (v3)

**Changes from v1 (Presentation 1) → v2 → v3:**
- `Model` abstract class replaced by concrete `CDTPredictor` with real methods
- `RFModel` removed (RF was dropped, XGBoost used instead)
- `LSTMAttention` now mirrors actual PyTorch class
- Added `GraphState` (orchestrator's shared state object)
- Added `DAGOrchestrator` with fixed 5-node routing
- Added `FarmState` with 84-day `deque` sliding window
- Added `VirtualSensor` (standalone telemetry publisher)
- Added `ConnectionManager` (WebSocket broadcast utility)
- `SimulationEngine` merged into `CDTPredictor.monte_carlo()`
- `Dashboard` split into `App` + `LiveTwinSimulator` (React components)

```mermaid
classDiagram
    %% ── Domain Entities ──────────────────────────────────────────
    class District {
        -name: String
        -latitude: Float
        -longitude: Float
        -q1Threshold: Float
        +calculateQ1Threshold(yields: YieldRecord[]): Float
        +getHistoricalRecords(): List~YieldRecord~
    }

    class YieldRecord {
        -year: Int
        -season: String
        -area: Float
        -production: Float
        -yieldQAcre: Float
    }

    class TelemetryRecord {
        -date: String
        -T2M: Float
        -PRECTOTCORR: Float
        -RH2M: Float
        -GWETROOT: Float
    }

    %% ── Digital Twin State ───────────────────────────────────────
    class FarmState {
        -districtName: String
        -precipDeque: Deque~Float~         # maxlen=84
        -tempDeque: Deque~Float~            # maxlen=84
        -humidityDeque: Deque~Float~        # maxlen=84
        -soilMoistureDeque: Deque~Float~   # maxlen=84
        -lastPrediction: Dict
        -baselineTelemetry: Dict
        +appendRecord(record: Dict): void
        +aggregateToWeekly(): Dict          # 84 daily → 12 weekly
        +shouldRunInference(): Boolean      # every 7 records
    }

    %% ── ML Models ────────────────────────────────────────────────
    class LSTMAttention {
        -input_dim: Int
        -hidden_dim: Int                   # 64
        -n_layers: Int                     # 2
        -static_dim: Int                   # 11 (incl embedding)
        -seq_len: Int                      # 84
        -district_embedding: Embedding     # 30 districts → 8-dim
        -encoder: LSTM                     # 2-layer, dropout 0.2
        -attention: Sequential             # MLP → scalar score per step
        -pos_bias: Parameter               # learned positional bias
        -yield_head: Linear                # 16→1 regression
        -failure_head: Linear              # 16→1 binary logit
        +forward(x_seq, x_static): Tuple   # yield, failure_logit, attn_weights
    }

    class XGBRegressor {
        -n_estimators: Int                 # 500
        -max_depth: Int                    # 6
        -monotone_constraints: List~Int~   # [0, -1, 0, 0, ...]
        +predict(features): Float          # ~1ms inference
    }

    class XGBClassifier {
        -n_estimators: Int                 # 500
        +predict_proba(features): Array~Float~
    }

    class RidgeMetaLearner {
        -alpha: Float                      # 1.0
        -bounds: Tuple                     # (0.0, 1.0)
        +predict(base_preds): Float
    }

    class CDTPredictor {
        -dnn: LSTMAttention
        -xgb_reg: XGBRegressor
        -xgb_clf: XGBClassifier
        -meta_yield: RidgeMetaLearner       # stacking: [0.2L, 0.8X]
        -meta_fail: RidgeMetaLearner        # stacking: [0.68L, 0.32X]
        -seq_scaler: StandardScaler
        -xgb_scaler: StandardScaler
        -district_enc: LabelEncoder
        -season_enc: LabelEncoder
        -season_ohe: OneHotEncoder
        +predict(weather_48, district, season, year): Dict
        +monte_carlo(weather_48, district, season, year, n_samples=500): Dict
        +_prepare(weather_48, district, season, year): Tuple~seq, static, xgb~
        +_enable_dropout(): void
    }

    %% ── Orchestration Layer ──────────────────────────────────────
    class QueryType {
        <<enumeration>>
        YIELD_FORECAST
        FAILURE_RISK
        TEMPORAL_ANALYSIS
        WHAT_IF
        FULL_DIAGNOSIS
    }

    class GraphState {
        +district: String
        +season: String
        +year: Int
        +weather_48: np.ndarray
        +query_type: QueryType
        +xgb_yield: Optional~Float~
        +xgb_fail_prob: Optional~Float~
        +lstm_yield: Optional~Float~
        +lstm_fail_prob: Optional~Float~
        +lstm_attention: Optional~List~Float~~
        +mc_samples: Optional~List~Float~~
        +mc_ci: Optional~Dict~
        +mc_std: Optional~Float~
        +triggers: Optional~List~String~~
        +response: Optional~Dict~
    }

    class DAGOrchestrator {
        -predictor: CDTPredictor             # singleton, lazy-loaded
        +run(district, season, year, weather_48, query_type): Dict
        -node_xgb_yield(state): GraphState
        -node_xgb_failure(state): GraphState
        -node_lstm_attention(state): GraphState
        -node_mc_dropout(state): GraphState
        -node_triggers(state): GraphState
        -compile_response(state): Dict
    }

    %% ── Infrastructure ───────────────────────────────────────────
    class VirtualSensor {
        -telemetryDir: Path
        -publisherClient: StreamClient
        -startDate: String                  # "20240615"
        -delaySeconds: Float                # 1.5 sec/day
        +main(): void
        -on_connect(client, flags, rc): void
    }

    class ConnectionManager {
        -active_connections: List~WebSocket~
        +connect(ws: WebSocket): void
        +disconnect(ws: WebSocket): void
        +broadcast(message: String): void
    }

    class TelemetrySubscriber {
        -broker: String                     # message broker
        -port: Int                          # 1883
        -topic: String                      # odisha_cdt/telemetry/#
        -client: StreamClient
        +on_message(client, userdata, msg): void
        +start(): void
    }

    %% ── Associations ─────────────────────────────────────────────
    District "1" o-- "*" YieldRecord : has
    District "1" --> "1" FarmState : maintains twin
    FarmState "1" --> "1" CDTPredictor : invokes predict on
    FarmState ..> TelemetrySubscriber : fed by

    CDTPredictor "1" *-- "1" LSTMAttention : owns
    CDTPredictor "1" *-- "1" XGBRegressor : owns
    CDTPredictor "1" *-- "1" XGBClassifier : owns
    CDTPredictor "1" *-- "2" RidgeMetaLearner : owns
    CDTPredictor "1" ..> "1" DAGOrchestrator : used by

    DAGOrchestrator "1" *-- "1" GraphState : creates and mutates

    VirtualSensor ..> TelemetrySubscriber : publishes to topic
    TelemetrySubscriber ..> FarmState : updates state

    ConnectionManager "1" --> "*" WebSocket : manages connections
    TelemetrySubscriber ..> ConnectionManager : triggers broadcast
```

---

## 3. Sequence Diagram 1: Predict Crop Failure

**Flow:** User clicks a district → Frontend calls API → DAG routes to model nodes → Compiled response → Dashboard renders

**Shows:** The `full_diagnosis` route (all 5 nodes).

```mermaid
sequenceDiagram
    actor U as Agricultural Analyst
    participant UI as React Dashboard
    participant API as FastAPI Backend
    participant DAG as DAGOrchestrator
    participant XGB as XGBoost Node
    participant LSTM as LSTM+Attn Node
    participant MC as MC Dropout Node
    participant TRG as Triggers Node
    participant PRED as CDTPredictor

    U->>UI: Click district "Ganjam" on map
    UI->>UI: Get district coords + season info
    UI->>API: GET /api/predict/Ganjam/Kharif/2024

    activate API
    API->>API: telemetry_to_flat48(telemetry)
    API->>DAG: run("Ganjam", "Kharif", 2024, w48, FULL_DIAGNOSIS)

    activate DAG
    DAG->>DAG: Create GraphState(query_type=FULL_DIAGNOSIS)
    DAG->>DAG: Lookup route = [xgb_yield, xgb_failure, lstm, mc_dropout, triggers]

    DAG->>XGB: node_xgb_yield(state)
    activate XGB
    XGB->>PRED: _prepare(weather_48, district, season, year)
    XGB->>XGB: xgb_reg.predict(xgb_scaled)
    XGB-->>DAG: state.xgb_yield = 14.2
    deactivate XGB

    DAG->>XGB: node_xgb_failure(state)
    activate XGB
    XGB->>XGB: xgb_clf.predict_proba(xgb_scaled)
    XGB-->>DAG: state.xgb_fail_prob = 0.32
    deactivate XGB

    DAG->>LSTM: node_lstm_attention(state)
    activate LSTM
    LSTM->>PRED: dnn(seq_t, static_t)
    PRED-->>LSTM: yield, failure_logit, attention_weights
    LSTM-->>DAG: state.lstm_yield, state.lstm_fail_prob, state.lstm_attention
    deactivate LSTM

    DAG->>MC: node_mc_dropout(state)
    activate MC
    MC->>PRED: monte_carlo(weather_48, "Ganjam", "Kharif", 2024, 500)
    loop 500 times
        PRED->>PRED: dnn(seq_t, static_t) with dropout active
    end
    PRED-->>MC: {yield_distribution, CI, std}
    MC-->>DAG: state.mc_samples, state.mc_ci, state.mc_std
    deactivate MC

    DAG->>TRG: node_triggers(state)
    activate TRG
    TRG->>TRG: Check: soil<0.35→drought, temp>34→heat, precip>250→flood
    TRG-->>DAG: state.triggers = ["Drought Stress"]
    deactivate TRG

    DAG->>DAG: _compile_response(state)
    Note over DAG: Stack yield: [lstm×0.2 + xgb×0.8]<br/>Stack failure: [lstm×0.68 + xgb×0.32]
    DAG-->>API: {predicted_yield, failure_probability, active_triggers, attention_weights, confidence_interval, _trace}
    deactivate DAG

    API-->>UI: JSON Response
    deactivate API

    UI->>UI: Update district popup + metrics
    UI-->>U: See yield=14.2 Q/Acre, failure=32%, triggers="Drought"
```

---

## 4. Architecture Diagram (v2 — 4-Layer)

**Changes from v1 (Presentation 1):**
- Message Broker added as external component
- `VirtualSensor` publishes CSV replay → message broker → subscriber
- `FarmState` (deque buffers) added as persistent twin state
- `WebSocket /ws/farm-stream` replaces polling for live updates
- `React 19` replaces "Next.js", `Custom DAG` replaces "LangGraph"
- RF removed, XGBoost standalone with stacking meta-learner

```mermaid
graph TB
    subgraph L1["Layer 1: Physical Entity"]
        A("30 Odisha Districts")
        B("Farmers & Agronomy")
        C("Climate System")
    end

    subgraph L2["Layer 2: Data Acquisition"]
        D("Govt Yield CSVs") --> F("Data Harmonization")
        E("NASA POWER API\n(daily/hourly)") --> F
        F --> G("final_dataset.csv\n1,113 rows, 58 cols")
        G --> H("Telemetry CSVs\n30 × 16,587 daily rows")

        VS("VirtualSensor.py\n(1.5s/day replay)") --> PUBSUB("Message Broker")
        PUBSUB --> SUB("Telemetry Subscriber\n(on_message)")
        SUB --> FS("FarmState\n(84-day deques)")
        H --> VS
    end

    subgraph L3["Layer 3: Cognitive Analytics"]
        G --> PREP("prepare_data.py\nfeature engineering")
        PREP --> TRAIN("train.py\nLSTM + XGBoost + Stacking")

        TRAIN --> LSTM("LSTM+Attention\n84-step, 56K params")
        TRAIN --> XGB("XGBoost\n23 features, 500 trees")
        TRAIN --> META("Ridge Meta-Learner\n[0.2L/0.8X yield]\n[0.68L/0.32X fail]")

        LSTM --> DAG("DAG Orchestrator\n5 query types")
        XGB --> DAG
        META --> DAG

        FS --> DAG
        DAG --> TRG("Biophysical Triggers\nDrought/Heat/Flood/Pest")
    end

    subgraph L4["Layer 4: Application"]
        DAG --> API("FastAPI Backend\n17 endpoints")
        API --> LLM("Groq LLM\nllama-3.3-70b")
        API --> WS("WebSocket\n/ws/farm-stream")

        WS --> UI("React 19 + Vite 8")
        LLM --> UI
        API --> UI

        UI --> MAP("OdishaGISMap\n(Leaflet)")
        UI --> TWIN("LiveTwinSimulator\n(ComposedChart)")
        UI --> CHAT("DSSChat\n(advisory LLM)")
        UI --> FBL("FeedbackLoop\n(what-if)")
        UI --> MET("Metrics Cards")
    end

    L1 -. "NASA satellite\ntelemetry" .-> L2
    L4 -. "Advisories &\nWhat-If Feedback" .-> L1
```

---

## 5. State Diagram: FarmState Lifecycle

**Shows:** How the digital twin state evolves over time, transitioning through different phases as virtual sensor data streams in.

```mermaid
stateDiagram-v2
    [*] --> INITIALIZED: Backend starts

    INITIALIZED --> FILLING: First telemetry message received
    INITIALIZED --> IDLE: No stream active

    state FILLING {
        [*] --> WARMUP: deque < 84 records
        WARMUP --> WARMUP: Append daily record
        WARMUP --> STEADY_STATE: deque reaches 84
        STEADY_STATE --> STEADY_STATE: Append + pop (sliding window)
        STEADY_STATE --> WARMUP: Stream resets (clear deque)
    }

    FILLING --> AGGREGATING: Every 7th record
    AGGREGATING --> INFERRING: Weekly features ready
    INFERRING --> BROADCASTING: Prediction result ready
    BROADCASTING --> FILLING: Continue stream

    FILLING --> PAUSED: User pauses stream
    PAUSED --> FILLING: User resumes stream

    FILLING --> STOPPED: User stops stream
    PAUSED --> STOPPED: User stops stream
    STOPPED --> FILLING: User restarts stream

    STOPPED --> [*]: Backend shuts down
    IDLE --> FILLING: Stream starts
```

---

## Appendix: Comparison to Presentation 1 Diagrams

| Aspect | Presentation 1 (Planned) | Presentation 2 (Built) |
|--------|-------------------------|----------------------|
| **Use Cases** | 6 use cases, 2 actors | 9 use cases, 3 actors (+ message broker) |
| **Class Diagram** | Abstract `Model` → `RFModel`, `LSTMModel` | Concrete `CDTPredictor` with 5 sub-models, `DAGOrchestrator`, `FarmState` |
| **Sequence Diagrams** | 1 (Predict Crop Failure) | 1 (Predict Crop Failure via DAG) |
| **Architecture** | LangGraph + Next.js | Custom DAG + React 19 + message broker |
| **Unique Elements** | Planned UML-style | Real code-mapped: `GraphState`, `QueryType` enum, MC dropout, telemetry subscriber, streaming thread |
| **Actor Types** | Analyst, Farmer, NASA, Govt API | Analyst, Farmer, **Message Broker** (virtual infrastructure) |

