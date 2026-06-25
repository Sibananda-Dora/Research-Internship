# Detailed Functional Requirements (Input / Processing / Output)

This document details the precise mechanics of each functional requirement for the Cognitive Digital Twin (CDT) framework. It breaks down what data enters the system, how the system manipulates it, and what is produced.

### Quick Reference Table (For Presentation Slide)

| FR ID | Process Name | Input | Processing Mechanics | Output / Result |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | **Ingest Historical Data** | Raw UPAg/Govt yield CSVs (1997–2025) | Clean text, map seasons, and standardize yield to Quintals/Acre. | Structured historical database |
| **FR-02** | **Interpolate Data Gaps** | Harmonized database with missing years | Apply time-series interpolation (linear/polynomial) to estimate gaps. | Continuous 20-year yield grid |
| **FR-03** | **Calculate Thresholds** | Continuous 20-year grid | Group by district/season and calculate First Quartile ($Q_1$) thresholds. | Binary `Failure_Anomaly` labels |
| **FR-04** | **Fetch Satellite Telemetry** | District Coordinates & Dates | Execute API requests to NASA POWER for daily meteorological metrics. | Raw daily weather time-series |
| **FR-05** | **Merge Telemetry** | Yield labels + Daily weather | Aggregate weather into 12-week windows and inner join with yield. | Final ML Dataset (Tabular & 3D) |
| **FR-06** | **Train Predictive Models** | Final ML Dataset | Train Dual-Track router (RF+XGBoost and PyTorch LSTM-Attention). | Serialized model weights (`.pt`) |
| **FR-07** | **Predict Failure Risk** | Real-time 12-week weather | Run inference and extract LSTM temporal attention weights. | `PredictionResult` (Yield + Risk) |
| **FR-08** | **Visualise Summaries** | `PredictionResult` objects | Parse probabilities to render interactive GIS layers and metric cards. | Web Dashboard UI |
| **FR-09** | **Run What-If Simulations** | User-adjusted climate sliders | Apply perturbations to baseline data and run Monte Carlo simulations. | Counterfactual yield & risk metrics |
| **FR-10** | **Query Expert Chatbot** | Natural language questions | LangGraph agent fetches prediction context to prompt an LLM. | Plain-language agronomic advisory |
| **FR-11** | **Sync Seasonal Data** | Automated end-of-season trigger | API call to UPAg to download new real-world ground truth data. | Updated database & retrained model |

---

## FR-01: Ingest Historical Yield Data
*   **Input:** Raw agricultural census CSV files from the UPAg / Odisha Government containing unstructured yield records spanning 1997–2025.
*   **Processing:** The ETL pipeline cleans the data, standardizes district names (e.g., resolving spelling discrepancies like "Balasore" vs "Baleshwar"), maps seasons (Kharif/Rabi), and standardizes measurement units to quintals per acre (Q/Acre).
*   **Output:** A structured, harmonized database table of historical district-level yield records.

## FR-02: Interpolate Data Gaps
*   **Input:** The harmonized historical yield database containing missing years or incomplete seasonal records.
*   **Processing:** The system identifies chronological gaps per district and applies time-series interpolation (e.g., linear or polynomial) to mathematically estimate the missing yield values, ensuring a continuous time-step for machine learning.
*   **Output:** A mathematically continuous 20-year yield dataset (approximately 1,200 rows) with no missing values.

## FR-03: Calculate Anomaly Thresholds
*   **Input:** The continuous 20-year yield dataset.
*   **Processing:** The system groups the data by district and season, calculates the First Quartile ($Q_1$) of the historical yield distribution, and flags any yield falling below this threshold as an anomaly.
*   **Output:** A calculated $Q_1$ threshold per district and a binary `Failure_Anomaly` label (0 or 1) attached to every historical record.

## FR-04: Fetch Satellite Weather Telemetry
*   **Input:** District geographical coordinates (Latitude/Longitude), a specified date range (spanning the 12-week vegetative cycle), and requested parameter flags (e.g., `PRECTOTCORR`, `T2M`, `RH2M`, `GWETROOT`).
*   **Processing:** The system constructs and executes an API GET request to the NASA POWER Agroclimatology server, parses the JSON response, and automatically handles any API rate limits or connection retries.
*   **Output:** Raw, daily meteorological time-series data for each requested district.

## FR-05: Aggregate and Merge Telemetry
*   **Input:** Raw daily meteorological data from NASA POWER and the labeled historical yield records.
*   **Processing:** The data engineering pipeline rolls the daily weather data into 12-week temporal windows (computing weekly averages/sums for temperature, rainfall, etc.) and performs an inner join with the historical yield data based on the year and district.
*   **Output:** The final, merged Machine Learning dataset (formatted as tabular data for Track A, and 3D Tensors for Track B).

## FR-06: Train Predictive Models
*   **Input:** The final, merged Machine Learning dataset.
*   **Processing:** The Dual-Track ML Router feeds the tabular data into the Scikit-Learn Ensemble (Random Forest + XGBoost) and the temporal 3D data into the PyTorch LSTM-Attention network. The models mathematically adjust their internal weights to minimize prediction error over multiple epochs.
*   **Output:** Serialized model weight files (`.pkl` or `.pt`) representing the trained, intelligent "brain" of the Digital Twin.

## FR-07: Predict Crop Failure Risk
*   **Input:** Current or real-time 12-week weather telemetry vectors for a specific district.
*   **Processing:** The trained models perform a forward pass (inference) on the new data. Concurrently, the system extracts Temporal Attention weights to evaluate biophysical triggers (e.g., algorithmically identifying severe drought in week 4).
*   **Output:** A `PredictionResult` object containing the forecasted yield amount, the calculated probability of a failure anomaly, and the specific physical factors driving the risk.

## FR-08: Visualise District Summaries
*   **Input:** The `PredictionResult` objects generated across all monitored districts.
*   **Processing:** The React/Vite Frontend parses the risk probabilities and dynamically renders GIS map layers (color-coding districts by risk level), trend charts, and summary metric cards.
*   **Output:** An interactive, glassmorphism-styled Web Dashboard visible to the Agricultural Analyst and Farmer.

## FR-09: Run "What-If" Climate Simulations
*   **Input:** User-modified weather variables submitted via slider UI components on the dashboard (e.g., "+2°C Temperature" or "-20% Rainfall").
*   **Processing:** The Simulation Engine applies these perturbations to the baseline telemetry and feeds the modified data back through the ML models (Monte Carlo simulation approach) to generate a counterfactual scenario.
*   **Output:** Updated "What-If" prediction metrics showing exactly how the crop failure risk changes under the simulated conditions.

## FR-10: Query Expert Advisory Chatbot
*   **Input:** Natural language questions typed by the Farmer or Analyst (e.g., "What should I do about the high thermal stress in Ganjam?").
*   **Processing:** The LangGraph Orchestrator intercepts the query, fetches the latest `PredictionResult` context for the relevant district, and utilizes a Large Language Model (LLM) to formulate agronomic advice based on the identified biophysical triggers.
*   **Output:** A plain-language, actionable advisory or intervention recommendation displayed in the chat interface.

## FR-11: Sync Seasonal Yield Data (Feedback Loop)
*   **Input:** An automated cron trigger at the end of the agricultural season (Kharif/Rabi).
*   **Processing:** The system reaches out to the UPAg / Govt API to download the newly finalized, real-world ground truth yield data and appends it to the historical database.
*   **Output:** An updated foundational dataset that triggers a model re-training cycle, ensuring the Cognitive Digital Twin remains continuously accurate and adaptive over time.
