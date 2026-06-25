---
status: draft
created: 2026-06-21
method: Abbott's Noun-Verb Analysis (Textual Analysis)
---

# Noun-Verb Analysis — CPDT Crop Failure Prediction System

## Methodology

Using **Abbott's Technique** (1983), we systematically extract nouns and verbs from the system's requirements text to identify candidate **classes** (nouns), **methods/operations** (verbs), and **attributes** (adjectives/descriptors).

> **Source Text** (derived from the Problem Statement):
>
> *"The Cyber-Physical Digital Twin system ingests historical crop yield records and real-time satellite weather telemetry for 30 Odisha districts. It harmonizes raw yield data by standardising district names, aligning crop seasons, interpolating missing years, and converting yield units. It fetches daily weather telemetry from the NASA POWER API, aggregates daily records into 12 weekly feature windows matching the crop calendar, and merges the weather features with yield profiles. The system trains a Random Forest model and an LSTM-Attention model on the final dataset. A researcher selects a district and season, optionally provides current weather conditions, and the system predicts yield and classifies whether a crop failure anomaly is likely. The dashboard visualises district summaries, historical yield trends, and prediction results."*

---

## 1. Nouns → Candidate Classes & Actors

### Extraction and Filtering

| # | Noun (from text) | Category | Disposition | Rationale |
|---|---|---|---|---|
| 1 | Cyber-Physical Digital Twin | Fuzzy | **Discard** | System-level concept, not a class |
| 2 | Crop Yield Record | Relevant | **Class** → `YieldRecord` | Core data entity |
| 3 | Weather Telemetry | Relevant | **Class** → `TelemetryRecord` | Core data entity |
| 4 | District | Relevant | **Class** → `District` | Spatial entity (30 instances) |
| 5 | Season | Relevant | **Attribute** of `YieldRecord` | Only two values: Kharif, Rabi |
| 6 | NASA POWER API | Relevant | **Actor** (external system) | External data provider |
| 7 | Researcher / Analyst | Relevant | **Actor** (primary) | Human user of the system |
| 8 | Dataset | Relevant | **Class** → `Dataset` | The merged final dataset (1,200 × 58) |
| 9 | Random Forest Model | Relevant | **Class** → `RFModel` | Track A prediction engine |
| 10 | LSTM-Attention Model | Relevant | **Class** → `LSTMModel` | Track B prediction engine |
| 11 | Prediction Result | Relevant | **Class** → `PredictionResult` | Output object |
| 12 | Dashboard | Relevant | **Class** → `Dashboard` | Visualisation interface |
| 13 | Weekly Feature Window | Relevant | **Attribute** of `TelemetryRecord` | 12-week aggregated features |
| 14 | Q1 Threshold | Relevant | **Attribute** of `District` | Anomaly detection boundary |
| 15 | Failure Anomaly | Relevant | **Attribute** of `PredictionResult` | Boolean classification label |

### Final Nouns (Actors)

| Actor | Type | Description |
|---|---|---|
| **Researcher** | Primary (human) | Initiates pipelines, views dashboards, runs predictions |
| **NASA POWER API** | Secondary (external system) | Provides daily satellite weather data on request |

### Final Nouns (Candidate Classes)

| Class | Description | Key Attributes |
|---|---|---|
| `District` | One of 30 Odisha administrative regions | `-name: String`, `-latitude: Float`, `-longitude: Float`, `-q1Threshold: Float` |
| `YieldRecord` | A single crop season yield entry | `-year: Int`, `-season: String`, `-area: Float`, `-production: Float`, `-yieldMTha: Float`, `-yieldQAcre: Float`, `-isInterpolated: Boolean` |
| `TelemetryRecord` | Daily weather data for one district | `-date: Date`, `-precipitation: Float`, `-temperature: Float`, `-humidity: Float`, `-soilWetness: Float` |
| `Dataset` | The final merged ML-ready dataset | `-records: List<YieldRecord>`, `-shape: Tuple(rows, cols)`, `-districts: List<District>` |
| `RFModel` | Random Forest predictor (Track A) | `-nEstimators: Int`, `-featureImportances: List<Float>`, `-isTrained: Boolean` |
| `LSTMModel` | LSTM-Attention predictor (Track B) | `-hiddenSize: Int`, `-attentionWeights: List<Float>`, `-isTrained: Boolean` |
| `PredictionResult` | Output of a prediction request | `-predictedYield: Float`, `-failureProbability: Float`, `-riskLevel: String`, `-contributingFactors: List<String>` |
| `Dashboard` | The web-based visualisation layer | `-districtCards: List`, `-charts: List`, `-predictionConsole: Component` |

---

## 2. Verbs → Candidate Methods / Operations

All method names follow the **verb-first** naming convention (e.g., `fetchData()`, not `dataFetch()`), as specified in the project requirements.

### Extraction

| # | Verb Phrase (from text) | Assigned To | Method Signature |
|---|---|---|---|
| 1 | Harmonise yield data | `YieldRecord` (or processor) | `+harmoniseData(rawCSV): YieldRecord[]` |
| 2 | Standardise district names | `District` | `+standardiseName(rawName): String` |
| 3 | Align crop seasons | `YieldRecord` | `+alignSeason(rawSeason): String` |
| 4 | Interpolate missing years | `Dataset` | `+interpolateGaps(districtGroup): YieldRecord[]` |
| 5 | Convert yield units | `YieldRecord` | `+convertToQAcre(yieldMTha): Float` |
| 6 | Fetch daily telemetry | `TelemetryRecord` (or fetcher) | `+fetchTelemetry(district, startDate, endDate): TelemetryRecord[]` |
| 7 | Aggregate weekly features | `TelemetryRecord` | `+aggregateWeekly(dailyData, windowStart): Map<String, Float>` |
| 8 | Merge datasets | `Dataset` | `+mergeYieldWithTelemetry(yields, telemetry): Dataset` |
| 9 | Calculate anomaly threshold | `District` | `+calculateQ1Threshold(yields): Float` |
| 10 | Train model | `RFModel` / `LSTMModel` | `+trainModel(dataset): void` |
| 11 | Predict crop failure | `RFModel` / `LSTMModel` | `+predictFailure(features): PredictionResult` |
| 12 | Visualise district summary | `Dashboard` | `+renderDistrictCards(districts): void` |
| 13 | Display yield trend | `Dashboard` | `+displayYieldTrend(records): void` |
| 14 | Run prediction | `Dashboard` | `+submitPrediction(district, season, telemetry?): PredictionResult` |

### Verbs as Relationships (connecting two nouns)

| Verb | Subject → Object | Relationship Type |
|---|---|---|
| "ingests" | System → YieldRecord, TelemetryRecord | Association |
| "trains on" | RFModel/LSTMModel → Dataset | Dependency |
| "belongs to" | YieldRecord → District | Association |
| "generates" | RFModel/LSTMModel → PredictionResult | Dependency |
| "visualises" | Dashboard → PredictionResult, YieldRecord | Association |
