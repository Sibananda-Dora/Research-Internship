# Progress Review Meeting - 1 (PPT Content)
**Tentative Date:** 23/06/2026

This document contains all the detailed text, tables, and UML diagrams mapped exactly to the `Slide_format1.docx` flow. You can copy and paste this directly into your presentation slides.

---

## Slide 1: Title & Group Members
**Title:** Development of a Cognitive Digital Twin Framework for Crop Yield Forecasting and Climate-Induced Failure Anomaly Detection
**Project Scope:** Odisha Pilot Engine (District-Stratified)
**Group Members:**
- [Insert Name 1]
- [Insert Name 2]
- [Insert Name 3]

---

## Slide 2: Planning Phase

### 2.1 Problem Domain
- **Primary Domain:** Agricultural Technology (AgriTech) & Artificial Intelligence
- **Sub-Domains:** Cognitive Digital Twins (CDT), Predictive Analytics, Deep Learning (LSTM), Remote Sensing (Satellite Telemetry).
- **Core Focus:** Building a continuous, data-driven feedback loop for proactive crop failure detection.

### 2.2 Problem Description (100-200 words)
Currently, agricultural yield forecasting relies heavily on retrospective government statistics that lack real-time predictive capabilities. When climate-induced anomalies—such as severe droughts, extreme thermal stress, or flooding—occur, traditional regression models fail to accurately classify the probability of a crop failure in time for intervention. Furthermore, "black box" deep learning models provide predictions without actionable explanations, reducing trust among stakeholders. There is a critical need for an intelligent system that can continuously ingest environmental telemetry, model biophysical failure triggers, account for weather uncertainty, and provide explainable AI insights. A Cognitive Digital Twin (CDT) solves this by replicating the physical agricultural state digitally, allowing for proactive decision-making and counterfactual "What-If" climate simulations.

### 2.3 Literature Reviews
- **Andini & Utomo (2021)**: Utilized RNN-LSTM networks for 1-month climate forecasting, achieving a 3.29% MAPE. *Limitation*: Only forecasted climate, not crop yield.
- **Yan et al. (2025)**: Proposed a Weighted Ensemble of Random Forest and XGBoost for crop yield time-series data, significantly reducing mean absolute error. *Limitation*: Predicted continuous yield volume but ignored binary disaster classification.
- **Kenneth (2026)**: Developed "CropTwin," utilizing the NASA POWER API and Monte Carlo simulations to handle weather uncertainty. *Limitation*: Ignored biotic stress factors (pests/diseases).
- **Arya et al. (2026)**: Developed a Hybrid Multi-Model ML Framework (ETS-ANN and LSTM) highlighting high predictive accuracy for staple crops (Rice) vs. high variability in others. 

### 2.4 Research Gaps
1. **The Labeling Gap**: Existing research predicts pure yield volume ($t/ha$), whereas disaster relief requires binary classification of a "Failure Anomaly."
2. **The Explainability Gap**: Deep learning models act as a "black box." There is a need to map mathematical features (LSTM attention weights) to real-world biophysical triggers (drought, thermal sterility).
3. **The Macro-to-Micro Bridge**: High infrastructure costs prevent local sensor deployment for smallholders. District-stratified macro-data (NASA POWER) must be accurately transformed into field-level risk proxies.

### 2.5 Problem Statement (2-3 lines)
*Note: This was labeled as 2.3 in the docx by mistake.*
To design and develop a Cognitive Digital Twin that integrates 20 years of historical yield data with continuous NASA POWER weather telemetry to accurately forecast crop yield, classify failure anomalies using a dual-track ML/DL engine, and provide explainable decision support via "what-if" simulations.

---

## Slide 3: Analysis Phase

### 3.1 Functional Requirements (Tabular Format)
*Copy this table directly into your slide.*

| FR ID | Name | Input | Output / Result |
|---|---|---|---|
| **FR-01** | **Ingest Historical Data** | Raw district yield CSVs (1997-2025) | Standardised, aggregated yield records |
| **FR-02** | **Interpolate Data Gaps** | Yield records with missing years | Continuous 20-year grid (1,200 rows) |
| **FR-03** | **Calculate Anomalies** | Interpolated 20-year dataset | $Q_1$ thresholds & Binary Failure labels |
| **FR-04** | **Fetch Weather Telemetry** | District coordinates, Date range | Cached NASA POWER daily CSVs |
| **FR-05** | **Aggregate 12-Week Window**| Yield records + Daily telemetry | Merged ML dataset (1,200 rows × 58 cols) |
| **FR-06** | **Train Predictive Models** | Merged dataset (Tabular & 3D Tensor) | Serialized RF/XGB and LSTM model weights |
| **FR-07** | **Predict Crop Failure** | Telemetry vectors + Season/District | Yield prediction, Failure probability, Risk |
| **FR-08** | **Visualise Summaries** | Prediction results | Interactive Map, District Cards, Trend Lines |
| **FR-09** | **Run What-If Simulations** | User-adjusted climate sliders | Counterfactual yield & risk prediction |

### 3.2 Technology Stack Requirements
- **Data Engineering**: Python, Pandas, NumPy, NASA POWER API (Agroclimatology).
- **Machine Learning (Track A & B)**: Scikit-Learn (Random Forest, XGBoost), PyTorch / TensorFlow (LSTM + Temporal Attention Layer).
- **Backend / Orchestration**: FastAPI (REST endpoints), LangGraph (Agentic DSS & Guardrails).
- **Frontend / Visualisation**: React + Vite, Recharts, Leaflet GIS, Custom SVG, Vanilla CSS (Glassmorphism).

---

## Slide 4: Design Phase

### 4.1 System Model / Architecture
*This diagram shows the 4-layer Cognitive Digital Twin architecture.*

```mermaid
graph TD
    subgraph L1 [Layer 1: Physical Entity Layer]
        A(Odisha Districts) --- B(Farmers & Agronomic Practices)
        B --- C(Climate System)
    end

    subgraph L2 [Layer 2: Data Acquisition Layer]
        D[(Govt. Yield Data)] --> F(Data Harmonization)
        E[(NASA POWER API)] --> F
        F --> G[(final_dataset.csv)]
    end

    subgraph L3 [Layer 3: Cognitive Analytics Layer]
        G -->|Tabular Data| H(Track A: RF+XGB Ensemble)
        G -->|3D Tensor| I(Track B: LSTM-Attention)
        I --> J(Biophysical Failure Triggers)
        I --> K(Monte Carlo Simulator)
    end

    subgraph L4 [Layer 4: Application Layer]
        H --> L{LangGraph Orchestrator}
        J --> L
        K --> L
        L --> M[Agentic DSS & Dashboard]
    end

    L1 -. "Sensors/Reports" .-> L2
    M -. "Advisories & What-If Scenarios" .-> L1
```

### 4.2 Use-Case Diagram
*This defines the system boundaries and actor interactions.*

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

### 4.3 Class Diagram
*Extracted via OOAD Abbott's Technique, identifying the core data structures and operations.*

```mermaid
classDiagram
    %% Core Domain Entities
    class District {
        -name: String
        -latitude: Float
        -longitude: Float
        -q1Threshold: Float
        +calculateQ1Threshold(yields: YieldRecord[]): Float
    }

    class YieldRecord {
        -year: Int
        -season: String
        -area: Float
        -production: Float
        -yieldMTha: Float
        -yieldQAcre: Float
        +convertToQAcre(yieldMTha: Float): Float
    }

    class TelemetryRecord {
        -date: Date
        -precipitation: Float
        -temperature: Float
        -humidity: Float
        -soilWetness: Float
        +aggregateWeekly(dailyData: TelemetryRecord[]): Map~String, Float~
    }

    class Dataset {
        -shape: Tuple
        +mergeYieldWithTelemetry(yields, telemetry): Dataset
    }

    %% AI / ML Engine
    class Model {
        <<abstract>>
        -isTrained: Boolean
        +trainModel(dataset: Dataset): void
        +predictFailure(features: Map~String, Float~): PredictionResult
    }

    class RFModel {
        -nEstimators: Int
        -featureImportances: List~Float~
    }

    class LSTMModel {
        -hiddenSize: Int
        -attentionWeights: List~Float~
    }

    class PredictionResult {
        -predictedYield: Float
        -failureProbability: Float
        -riskLevel: String
        -contributingFactors: List~String~
    }

    %% DSS and Application Layer
    class SimulationEngine {
        -baselineFeatures: Map~String, Float~
        +runWhatIfScenario(modifiedFeatures: Map): PredictionResult
    }

    class DSSChatbot {
        -contextHistory: List~String~
        +generateAdvisory(prediction: PredictionResult): String
        +answerQuery(question: String): String
    }

    class Dashboard {
        -districtCards: List
        +renderUI(districts: District[]): void
        +submitPredictionRequest(district, season, telemetry): void
    }

    %% Inheritance
    Model <|-- RFModel
    Model <|-- LSTMModel

    %% Composition / Aggregation
    Dataset "1" *-- "*" YieldRecord : contains
    Dataset "1" *-- "*" TelemetryRecord : contains
    District "1" o-- "*" YieldRecord : has

    %% Associations & Dependencies
    Dashboard "1" *-- "1" DSSChatbot : embeds
    Dashboard "1" *-- "1" SimulationEngine : uses
    SimulationEngine "1" ..> "1" Model : invokes
    DSSChatbot "1" ..> "1" PredictionResult : analyzes
    Model "1" ..> "1" PredictionResult : generates
    Model "1" ..> "1" Dataset : trains on
```

### 4.4 Sequence Diagram
*Shows the behavioral timeline for the "Predict Crop Failure" (UC7) operation.*

```mermaid
sequenceDiagram
    actor R as Researcher
    participant D as :Dashboard
    participant M as :LSTMModel
    participant T as :TelemetryRecord
    participant API as NASA POWER API
    participant PR as :PredictionResult

    R->>D: submitPrediction("Ganjam", "Kharif")
    activate D
    
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

    D->>M: predictFailure(weeklyFeatures)
    activate M
    
    M->>M: runTensorForwardPass(weeklyFeatures)
    M->>M: evaluateBiophysicalTriggers()
    
    M-->>PR: create(predictedYield, riskLevel)
    activate PR
    PR-->>M: PredictionResult Object
    deactivate PR
    
    M-->>D: return PredictionResult
    deactivate M
    
    D->>D: renderDistrictCards(PredictionResult)
    D-->>R: Display Failure Risk & Yield Forecast
    deactivate D
```

---

## Slide 5: Conclusion & Roadmap

**Conclusion:**
The Cognitive Digital Twin framework successfully bridges the gap between static yield reporting and proactive failure anomaly detection. By integrating 20 years of harmonised data with automated NASA satellite telemetry, the system provides an explainable, interactive Decision Support System (DSS). It empowers stakeholders to evaluate counterfactual "what-if" scenarios, transforming agricultural crisis response into resilience planning.

**Roadmap (Next Steps):**
- **Phase 1:** Data Engineering Pipeline & Telemetry Ingestion (Completed).
- **Phase 2:** Model Training (RF & LSTM-Attention) & Validation.
- **Phase 3:** LangGraph Agent Integration & Explainability Triggers.
- **Phase 4:** Frontend GIS Dashboard Deployment & User Testing.

---

## Slide 6: References
1. Abbott, R. J. (1983). *Program Design by Informal English Descriptions*.
2. Andini, A. & Utomo, P. (2021). *Climate Prediction Using RNN LSTM to Estimate Agricultural Products*.
3. Yan et al. (2025). *Crop Yield Time-Series Data Prediction Based on Multiple Hybrid ML Models*.
4. Kenneth. (2026). *Digital Twin-Based Uncertain Weather Condition Monitoring for Enhanced Crop Yield Prediction*.
5. Arya et al. (2026). *A Time-Series Hybrid Multi-Model ML Framework for Staple Crops Yield Prediction*.
6. NASA POWER Agroclimatology Data Access Viewer & API Documentation.
