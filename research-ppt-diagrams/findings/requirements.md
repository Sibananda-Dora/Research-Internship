---
status: draft
created: 2026-06-21
---

# Functional Requirements — Cognitive Digital Twin (CDT) for Crop Failure Prediction

Each functional requirement defines **what the system does**: what data it takes in, what processing occurs, and what output is produced.

---

## FR-01: Ingest Historical Crop Yield Data

| Field | Detail |
|---|---|
| **Input** | Raw CSV files containing district-level Area, Production, and Season records from government statistics (1997–2019 historical + 2024–25 DES estimates) |
| **Processing** | Standardise district spelling variants to 30 canonical names; collapse redundant season labels (Autumn, Winter → Kharif; Summer → Rabi); filter to the 2006–2025 window; aggregate Area and Production by (District, Year, Season) |
| **Output** | Cleaned, standardised yield records ready for gap-filling |

**Identifiable Verbs/Functions**: `standardiseName()`, `alignSeason()`, `filterYearRange()`, `aggregateYield()`

---

## FR-02: Interpolate Missing Yield Records

| Field | Detail |
|---|---|
| **Input** | Cleaned yield records with gaps for years 2020–2023 and 2025 |
| **Processing** | Generate a complete grid of 30 districts × 20 years × 2 seasons (= 1,200 rows); perform linear interpolation on Area and Production grouped by (District, Season); flag interpolated rows with `Is_Interpolated = True` |
| **Output** | Continuous 20-year yield dataset with zero missing values |

**Identifiable Verbs/Functions**: `generateGrid()`, `interpolateGaps()`, `flagInterpolated()`

---

## FR-03: Calculate Yield and Anomaly Thresholds

| Field | Detail |
|---|---|
| **Input** | Interpolated yield dataset |
| **Processing** | Compute yield in MT/ha (with division-by-zero protection where Area = 0); convert to Quintals/Acre using the formula: `Yield_Q_Acre = (Yield_MTha × 10) / 2.471`; calculate the Q1 (25th percentile) threshold per (District, Season); label `Failure_Anomaly = 1` if yield < Q1, else `0` |
| **Output** | `harmonized_yield.csv` — 1,200 rows with yield, threshold, and anomaly labels |

**Identifiable Verbs/Functions**: `calculateYield()`, `convertUnits()`, `calculateQ1Threshold()`, `labelAnomaly()`

---

## FR-04: Fetch Satellite Weather Telemetry

| Field | Detail |
|---|---|
| **Input** | 30 district centroid coordinates (latitude, longitude); date range (2006-01-01 to 2026-05-31) |
| **Processing** | Query the NASA POWER API (Agroclimatology community) for daily values of PRECTOTCORR, T2M, RH2M, and GWETROOT; cache raw responses as one CSV per district; handle retries and rate-limit pauses |
| **Output** | 30 cached CSV files in `sources/data/telemetry/{district}_daily.csv` |

**Identifiable Verbs/Functions**: `fetchTelemetry()`, `cacheResponse()`, `retryOnFailure()`

---

## FR-05: Aggregate and Merge Telemetry with Yield Data

| Field | Detail |
|---|---|
| **Input** | 1,200 harmonised yield records + 30 cached daily telemetry CSVs |
| **Processing** | For each yield record, isolate the 84-day vegetative window (Kharif: Jun 15–Sep 6; Rabi: Jan 1–Mar 25 of Y+1); group 84 days into 12 consecutive weeks; aggregate precipitation by SUM and temperature/humidity/soil-wetness by MEAN per week; join the 48 weekly features with the 10 yield columns |
| **Output** | `final_dataset.csv` — 1,200 rows × 58 columns (the ML-ready dataset) |

**Identifiable Verbs/Functions**: `extractVegetativeWindow()`, `aggregateWeekly()`, `mergeDatasets()`

---

## FR-06: Train Predictive Models

| Field | Detail |
|---|---|
| **Input** | `final_dataset.csv` (1,200 × 58); Track A uses the flat 48-feature vector; Track B reshapes into a 3D tensor of shape (1200, 12, 4) |
| **Processing** | **Track A**: Train a weighted Random Forest + XGBoost ensemble on tabular features; **Track B**: Train a stacked LSTM with temporal attention on the 12-step sequence; cross-validate with stratified district splits |
| **Output** | Serialised model weights; feature importance rankings (Track A); attention weight vectors (Track B) |

**Identifiable Verbs/Functions**: `trainRFModel()`, `trainLSTMModel()`, `crossValidate()`, `saveModelWeights()`

---

## FR-07: Predict Crop Failure for a Given District and Season

| Field | Detail |
|---|---|
| **Input** | User-selected district name, season (Kharif/Rabi), and optionally 12 weeks of current weather telemetry |
| **Processing** | If telemetry is provided, feed it through the trained model(s); compare predicted yield against the Q1 threshold; evaluate biophysical triggers (drought, heat stress, pest risk, flooding); run Monte Carlo dropout passes for confidence intervals |
| **Output** | `PredictionResult` object containing: predicted yield (Q/Acre), failure probability, risk level (LOW/MODERATE/HIGH), contributing stress factors, and confidence score |

**Identifiable Verbs/Functions**: `predictFailure()`, `evaluateTriggers()`, `runMonteCarlo()`, `classifyRisk()`

---

## FR-08: Visualise District Summaries and Historical Trends

| Field | Detail |
|---|---|
| **Input** | API response data from `/api/districts` and `/api/district/{name}` |
| **Processing** | Render 30 district cards with average yield, failure rate, and risk status; display interactive line charts of yield trends over 20 years with Q1 threshold overlay; provide season filters (Kharif/Rabi); colour-code districts on an interactive map |
| **Output** | Dashboard page with district grid, charts, and choropleth map |

**Identifiable Verbs/Functions**: `renderDistrictCards()`, `displayYieldTrend()`, `renderChoroplethMap()`, `filterBySeason()`

---

## FR-09: Run What-If Climate Simulations

| Field | Detail |
|---|---|
| **Input** | User-adjusted climate sliders (precipitation, temperature, humidity, soil wetness) for specific weeks within a 12-week window |
| **Processing** | Construct a modified telemetry tensor from the slider values; feed through the frozen LSTM model; compute the counterfactual prediction and compare against the baseline |
| **Output** | Side-by-side prediction comparison showing baseline vs. simulated yield and risk level |

**Identifiable Verbs/Functions**: `constructModifiedTensor()`, `runSimulation()`, `compareScenarios()`

---

# Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| **NFR-01** | **Reliability** | The data pipeline shall handle NASA POWER API failures gracefully with automatic retries (up to 3 attempts per district) and local caching to prevent data loss |
| **NFR-02** | **Performance** | The prediction endpoint (`/api/predict`) shall return results within 3 seconds for a single district-season query under normal load |
| **NFR-03** | **Scalability** | The data schema and pipeline shall support extension to additional states (beyond Odisha) and crop types (beyond Rice) without architectural changes |
| **NFR-04** | **Usability (HCI)** | The dashboard shall be usable without prior training; all charts shall include axis labels, legends, and tooltips; the prediction console shall provide clear risk visualisation |
| **NFR-05** | **Security** | All API inputs shall be validated and sanitised; the backend shall reject out-of-range telemetry values (e.g., negative precipitation, temperature outside −50°C to +60°C) |
| **NFR-06** | **Maintainability** | The codebase shall follow a modular architecture: separate scripts for data ingestion, harmonisation, merging, and serving; each module shall be independently testable |
| **NFR-07** | **Accuracy** | Trained models shall achieve a minimum classification F1-score of 0.70 on crop failure detection and regression RMSE within ±15% of observed yield variance |
| **NFR-08** | **Portability** | The system shall run on Windows 10+, macOS 12+, and Ubuntu 20.04+ using Python 3.10+ and Node.js 18+ |
| **NFR-09** | **Data Integrity** | The harmonised dataset shall contain exactly 1,200 rows with zero missing values; interpolated records shall be explicitly flagged |
