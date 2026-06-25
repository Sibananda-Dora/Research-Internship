---
status: verified
created: 2026-06-21
methodology: OOAD (Abbott's Technique)
---

# UML Diagrams for Cognitive Digital Twin (CDT)

These UML diagrams define the architecture of the Crop Failure Prediction System using strict Object-Oriented Analysis and Design (OOAD) principles. The design derives from Abbott's Noun-Verb Analysis and aligns completely with the project's Functional Requirements.

---

## 1. Use Case Diagram (Functional View)

This diagram visualizes the system's external actors, the system boundary, and the nine primary functional requirements identified as Use Cases. It employs standard `«include»` relationships to show mandatory sub-processes.

```mermaid
flowchart LR
    %% Actors (The "Who")
    A(("Agricultural Analyst\n(Primary User)"))
    F(("Farmer\n(End User)"))
    NASA(("NASA POWER API\n«External System»"))
    GOVT(("UPAg / Govt API\n«External System»"))

    %% System Boundary
    subgraph DSS ["Decision Support System (DSS) Web Platform"]
        direction TB
        UC1(["View District Yield Trends"])
        UC2(["Check Crop Failure Risk"])
        UC3(["Run 'What-If' Climate Simulations"])
        UC4(["Query Expert Advisory Chatbot"])
        UC5(["Fetch Real-Time Weather Data"])
        UC6(["Sync Seasonal Yield Data"])
    end

    %% What the Analyst can do
    A --- UC1
    A --- UC2
    A --- UC3
    A --- UC4
    
    %% What the Farmer can do (simpler access)
    F --- UC2
    F --- UC4
    
    %% What the External APIs do
    NASA --- UC5
    GOVT --- UC6
    
    %% System Logic (Dependencies)
    UC2 -. "«include»" .-> UC5
    UC3 -. "«extend»" .-> UC2
```

---

## 2. Class Diagram (Structural View)

Generated directly from **Abbott's Noun-Verb Analysis**, this diagram details the candidate classes, their private (`-`) attributes, public (`+`) methods, and structural relationships (Composition, Aggregation, Inheritance, and Dependency).

```mermaid
classDiagram
    %% Domain Models (Pydantic / DataClasses)
    class DistrictInfo {
        -name: String
        -latitude: Float
        -longitude: Float
        -q1Threshold: Float
    }

    class PredictionResponse {
        -yieldForecast: Float
        -failureProbability: Float
        -riskLevel: String
        -physicalTriggers: List~String~
    }

    class SimulationRequest {
        -tempOffset: Float
        -humidityOffset: Float
    }

    %% Service / Pipeline Classes
    class DataIngestionPipeline {
        +cleanYieldData()
        +interpolateGaps()
        +calculateQ1Thresholds()
    }

    class NASAAPIClient {
        -baseUrl: String
        -apiKey: String
        +fetchDailyTelemetry()
        +aggregateToWeeklyTensors()
    }

    %% ML Engine Classes
    class PredictionEngine {
        <<abstract>>
        -isTrained: Boolean
        +train()
        +predict()
    }

    class TabularRFModel {
        -nEstimators: Int
    }

    class TemporalLSTMModel {
        -hiddenSize: Int
        -attentionWeights: List~Float~
    }

    %% Application / DSS Classes
    class SimulationEngine {
        +runMonteCarlo()
    }

    class LangGraphOrchestrator {
        -llmClient: Object
        +generateAdvisory()
    }

    class FastAPIController {
        +getPrediction()
        +postSimulation()
    }

    %% Inheritance
    PredictionEngine <|-- TabularRFModel
    PredictionEngine <|-- TemporalLSTMModel
    
    %% Composition (Strong lifecycle dependency)
    FastAPIController "1" *-- "1" LangGraphOrchestrator : integrates
    FastAPIController "1" *-- "1" SimulationEngine : integrates
    FastAPIController "1" *-- "1" NASAAPIClient : integrates
    
    %% Aggregation (Weak lifecycle dependency)
    SimulationEngine "1" o-- "1" PredictionEngine : loads
    DataIngestionPipeline "1" o-- "*" DistrictInfo : manages
    
    %% Association (Uses / Interacts with)
    SimulationEngine "1" --> "*" SimulationRequest : processes
    LangGraphOrchestrator "1" --> "*" PredictionResponse : interprets
    NASAAPIClient "1" --> "*" DistrictInfo : fetches for
    PredictionEngine "1" --> "*" PredictionResponse : generates
```

---

## 3. Sequence Diagram (Behavioral View)

This diagram tracks the chronological flow and lifecycle of the **Predict Crop Failure** (UC7) operation. It utilizes lifelines, activation execution boxes, synchronous calls (solid arrows), return messages (dashed arrows), and an `alt/opt` interaction frame.

```mermaid
sequenceDiagram
    actor R as Researcher
    participant D as :Dashboard
    participant M as :LSTMModel
    participant T as :TelemetryRecord
    participant API as NASA POWER API
    participant PR as :PredictionResult

    %% Initial Call
    R->>D: submitPrediction("Ganjam", "Kharif")
    activate D
    
    %% Optional block for data fetching
    opt [Current weather not provided]
        D->>T: fetchTelemetry("Ganjam", startDate, endDate)
        activate T
        
        T->>API: GET /api/temporal/daily/point
        activate API
        API-->>T: JSON Daily Weather
        deactivate API
        
        T->>T: aggregateWeekly()
        T-->>D: Map<String, Float> weeklyFeatures
        deactivate T
    end

    %% Prediction Logic
    D->>M: predictFailure(weeklyFeatures)
    activate M
    
    M->>M: runTensorForwardPass(weeklyFeatures)
    M->>M: evaluateBiophysicalTriggers()
    
    %% Object Creation
    M-->>PR: create(predictedYield, riskLevel)
    activate PR
    PR-->>M: PredictionResult Object
    deactivate PR
    
    M-->>D: return PredictionResult
    deactivate M
    
    %% UI Update
    D->>D: renderDistrictCards(PredictionResult)
    D-->>R: Display Failure Risk & Yield Forecast
    deactivate D
```

---

## 4. System Architecture Diagram

This diagram outlines the 4-layer Cognitive Digital Twin architecture, mapping the real-world agricultural context through data acquisition, AI analytics, and finally to the user-facing Decision Support System (DSS).

```mermaid
flowchart TD
    %% Styling
    classDef physical fill:#e6f2ff,stroke:#4d94ff,stroke-width:2px;
    classDef data fill:#e6ffe6,stroke:#33cc33,stroke-width:2px;
    classDef analytics fill:#fff0e6,stroke:#ff8c1a,stroke-width:2px;
    classDef application fill:#f2e6ff,stroke:#9933ff,stroke-width:2px;

    %% Layer 1
    subgraph L1 ["1. Physical Entity Layer (Real World)"]
        direction LR
        P1[Odisha Districts]
        P2[Climate & Weather Patterns]
        P3[Farmers / Ground Reality]
        P1 ~~~ P2 ~~~ P3
    end
    class L1 physical;

    %% Layer 2
    subgraph L2 ["2. Data Acquisition & Harmonization Layer"]
        direction TB
        subgraph Sources
            A[(UPAg / Govt Historical Yield Data)]
            B[(NASA POWER Satellite Telemetry)]
        end
        C[[ETL Pipeline / Python Pandas]]
        D[(Harmonized 20-Year Dataset)]
        
        Sources -->|API & CSV Ingestion| C
        C -->|Interpolation & Q1 Thresholds| D
    end
    class L2 data;

    %% Layer 3
    subgraph L3 ["3. Cognitive Analytics Layer (AI Engine)"]
        direction TB
        E{Dual-Track ML Router}
        
        subgraph TrackA ["Track A: Baseline Forecasting"]
            F[Scikit-Learn Ensemble<br>RF + XGBoost]
        end
        
        subgraph TrackB ["Track B: Deep Temporal Learning"]
            G[PyTorch LSTM-Attention<br>3D Tensor Processing]
            H[Biophysical Trigger Mapping<br>Drought/Thermal Stress]
            G --> H
        end
        
        E -->|Tabular ML| F
        E -->|Temporal Deep Learning| G
    end
    class L3 analytics;

    %% Layer 4
    subgraph L4 ["4. Application & Orchestration Layer (DSS)"]
        direction TB
        I[[LangGraph Orchestrator / Expert Advisor]]
        J[[FastAPI Backend]]
        K[React + Vite Frontend Dashboard<br>GIS Maps & Trend Charts]
        L((End Users:<br>Analysts & Farmers))
        
        I <--> J
        J <--> K
        K <--> L
    end
    class L4 application;

    %% Connections Between Layers
    L1 -. "Real-world Metrics" .-> Sources
    D ==>|Feeds Training & Inference Data| E
    F -->|Yield Predictions| I
    H -->|Failure Anomaly Risks| I
    L4 -. "Actionable Advisories<br>& What-If Scenarios" .-> L1
```
