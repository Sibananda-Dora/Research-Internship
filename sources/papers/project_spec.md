# PROJECT WIKI CONTEXT SPECIFICATION
System Target: Digital Twin Knowledge Base / Expert Agent Context Mesh
Project Identity: CPDT-Crop-Failure-Prediction (Odisha Pilot Engine)

## 1. PROJECT EXECUTIVE SUMMARY & METADATA
Official Project Title: Development of a Cyber-Physical Digital Twin Framework for Joint Crop Yield Forecasting and Climate-Induced Failure Anomaly Detection via Multi-Agent Orchestration
Core Objective: To shift regional agricultural prediction away from isolated, static statistical models into an active, continuous, data-driven Cyber-Physical Digital Twin (CPDT).

### Dual-Task Optimization Architecture:
- **Regression Axis**: Precision continuous yield forecasting (Output: Quintals/Acre) utilizing 12-week macro-environmental time-series tensors.
- **Classification Axis**: Dynamic sequence-based anomaly detection predicting localized, high-risk crop failure events before they manifest.

## 2. GEOSPATIAL & TEMPORAL BOUNDARY CONDITIONS
- **Geographic Scope**: Odisha, India (State-level pilot).
- **Spatial Resolution Entity**: District-Stratified Resolution (30 distinct districts).
- **Temporal Scaling Depth**: 20 Years (2006 to 2026).
- **Dataset Geometry Size**: 30 districts x 20 years = 600 distinct profiles.

## 3. DATA INGESTION & SYNCHRONIZATION TIER (LAYER 2)
- **API**: NASA POWER API (Agroclimatology Community).
- **Sampling**: Daily values over an 84-day (12-week) window.
- **Core Features**:
    - `PRECTOTCORR`: Precipitation Corrected (mm/day).
    - `T2M`: Temperature at 2 Meters (°C).
    - `RH2M`: Relative Humidity (%).
    - `GWETROOT`: Root Zone Soil Wetness (%).

## 4. MATHEMATICAL LABEL ENGINEERING & TARGET DEFINITIONS
- **Continuous Target ($y_{reg}$)**: Actual Yield (Quintals/Acre) from UPAg Portal.
- **Categorical Target ($y_{class}$)**: Binary Failure Anomaly based on First-Quartile ($Q_1$) Thresholding per district.
- **Logic**: $y_{class} = 1$ if $y_{reg} < Q_1(Y_d)$, else 0.

## 5. COGNITIVE ANALYTICS & TENSOR MODELING ENGINE (LAYER 3)
- **Track A (Tabular ML)**: Random Forest Regressor on flattened seasonal statistics.
- **Track B (Deep Learning)**: Stacked LSTM with Temporal Attention (3D Tensor: 600 x 12 x 4).
- **Explainability**: Attention head maps weights ($a_1 \dots a_{12}$) to isolate failure weeks.

## 6. SERVICE & AGENT ORCHESTRATION TIER (LAYER 4)
- **Framework**: LangGraph State Machine (DAG).
- **Nodes**: Ingestion Node -> Execution Node -> Expert Advisory Node.
- **Guardrails**: LLM is blocked from action until numerical data is validated in the graph state.
