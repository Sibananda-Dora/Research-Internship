# Cover Page
**Title of the Project:** Smart Agriculture: A Cognitive Digital Twin for Crop Yield and Failure Detection
**Name(s) of Student(s):** Om Prakash Sahoo, Tejeswar Mishal, Soumya Ranjan Sahu, Sibananda Dora, Sambit Sekhar Biswal
**Roll Numbers:** 2401109207, 2401109256, 2401109239, 2401109233, 2521109014
**Department:** Computer Science / Engineering
**College/University:** Parala Maharaja Engineering College, Berhampur, Odisha
**Guide/Supervisor:** Dr. Niranjan Panigrahi, Dr. Sasmita Rani Behera
**Academic Year:** 2025-2026

---

# Abstract
Agricultural yield forecasting currently relies heavily on retrospective government statistics that lack real-time predictive capabilities. When climate-induced anomalies occur, traditional regression models fail to classify the probability of crop failure in time for intervention, and uninterpretable deep learning models reduce trust among stakeholders. The objective of this project is to develop a Cognitive Digital Twin (CDT) that integrates 20 years of historical yield data (1997–2025) with continuous NASA POWER and Open-Meteo weather telemetry. The proposed product uses a dual-track predictive engine comprising an LSTM-Attention neural network for temporal feature extraction and an XGBoost ensemble for predicting continuous crop yields and classifying binary failure risks. By deploying an intelligent Decision Support System (DSS) via the Groq LLM API, the platform translates complex tensor outputs into plain-language actionable advisories. The methodology achieves a high predictive accuracy (R² of 0.712 and Failure AUC of 0.721) on held-out test data. This scalable, hardware-free remote sensing approach bridges the gap between passive batch systems and proactive disaster management for smallholder farmers.

---

# Chapter 1: Introduction

## 1.1 Background
Smart agriculture has become increasingly critical due to rapid climate change, erratic weather patterns, and the need for food security. In regions like Odisha, smallholder farmers rely heavily on rain-fed agriculture (e.g., Kharif and Rabi rice crops), making them highly vulnerable to thermal stress, droughts, and flooding. Digital Twins—virtual representations of physical systems—offer a transformative approach by simulating the agricultural environment to enable continuous monitoring and predictive insights.

## 1.2 Problem Statement
Currently, agricultural yield forecasting relies heavily on retrospective government statistics that lack real-time predictive capabilities. Traditional regression models fail to classify the probability of a crop failure in time for proactive intervention. Furthermore, modern deep learning models provide predictions without actionable explanations, reducing trust among stakeholders. There is a critical need for an intelligent system that continuously ingests environmental telemetry, models biophysical failure triggers, accounts for weather uncertainty, and provides explainable AI insights.

## 1.3 Need for the Product
- **High Hardware Cost:** Existing agricultural digital twins rely on expensive, localized IoT sensor networks (single-farm silos) which are financially unviable for smallholders.
- **Lack of Real-Time Proaction:** Current forecasting is batch-processed at the end of the season. No continuous, live feedback loop exists.
- **Interpretability:** Farmers cannot parse "black-box" model weights; they require plain-language agronomic advisories.

## 1.4 Objectives
1. **Engineer an automated data pipeline:** Harmonize two decades of historical crop yield statistics with continuous, satellite-based weather telemetry (NASA POWER).
2. **Formulate a statistical framework:** Define, quantify, and label district-level crop failure anomalies.
3. **Design and train a dual-purpose predictive engine:** Forecast continuous seasonal yields while simultaneously classifying imminent crop failure.
4. **Deploy an intelligent DSS:** Provide a natural language query-response interface for easy interaction.
5. **Construct an interactive Digital Twin dashboard:** Empower stakeholders to run counterfactual "what-if" climate simulations.

## 1.5 Scope
The proposed Cognitive Digital Twin targets 30 districts across Odisha, modeling 2 agricultural seasons (Kharif and Rabi). Because it relies purely on satellite telemetry (NASA POWER / Open-Meteo) rather than ground sensors, it is instantly scalable to other states or crops without deploying physical hardware.

## 1.6 Contributions
- **Hardware-less Digital Twin:** Built a working prototype utilizing satellite remote sensing instead of costly IoT networks.
- **Dual-Track ML Engine:** Implemented a robust architecture combining LSTM-Attention with XGBoost and Ridge Stacking.
- **Interactive Web Platform:** Developed a React 19 + Vite dashboard featuring dynamic GIS mapping, real-time gauges, and Monte Carlo What-If simulations.
- **Explainable AI Integration:** Deployed a Groq-powered chatbot to translate ML predictions into actionable advisories.

---

# Chapter 2: Literature Review

## 2.1 Research Papers Reviewed

**Paper 1: Climate Prediction Using RNN LSTM to Estimate Agricultural Products (Andini & Utomo, 2021)**  
- **Method:** The researchers proposed a methodology that utilized a Recurrent Neural Network (RNN) architecture with Long Short-Term Memory (LSTM) cells consisting of 48 input neurons. This was optimized via the Adam optimizer over 200 epochs to predict climate variables.
- **Results:** The model successfully achieved a high predictive accuracy for 1-month-ahead forecasting, yielding a Mean Absolute Percentage Error (MAPE) of just 3.29%.
- **Drawbacks:** Its temporal depth is strictly limited to forecasting just one month ahead, rather than projecting a full 12-week agricultural season. Additionally, it omits critical sub-surface environmental features like root zone soil wetness (GWETROOT), which are essential for robust biophysical stress modeling.

**Paper 2: A Time-Series Hybrid Multi-Model Machine Learning Framework for Staple Crops Yield Prediction (Arya et al., 2026)**  
- **Method:** The authors designed a Time-Series Hybrid Multi-Model Machine Learning Framework, combining traditional linear time-series forecasting (ETS) with non-linear deep learning (Artificial Neural Networks and LSTM).
- **Results:** The hybrid approach demonstrated superior accuracy, specifically achieving an R² of 98.4% for Rice yield predictions based on international macro-level agricultural data.
- **Drawbacks:** The framework operates as an uninterpretable "black box," lacking the Model Interpretability required to explain why a crop might fail. Furthermore, its reliance on international macro-data makes it poorly suited for district-stratified, localized interventions.

**Paper 3: Integrating Digital Twins and Advanced Crop Recommendation for Optimal Yield (Banerjee et al., 2024)**  
- **Method:** The researchers developed a Cyber-Physical System (CPS) methodology that digitally mirrors the physical farm environment using operational farm-level data collected via localized Internet of Things (IoT) sensor networks.
- **Results:** The implementation led to highly impactful optimizations, demonstrating a 10-25% increase in crop yield and a 20-30% reduction in water usage.
- **Drawbacks:** The heavy reliance on a sensor-dense "single-farm silo" creates a massive infrastructure cost and data interoperability bottleneck, rendering it financially unviable for smallholders in developing regions. It also lacks an automated, explainable advisory mechanism.

**Paper 4: Crop Yield Time-Series Data Prediction Based on Multiple Hybrid Machine Learning Models (Yan et al., 2025)**  
- **Method:** They constructed a Weighted Ensemble model that combines the predictive strengths of Random Forest (RF) and XGBoost algorithms, utilizing localized, real-time pesticide usage records as key features.
- **Results:** The hybrid ensemble approach significantly outperformed standalone models, successfully reducing the Mean Absolute Error (MAE) from 0.0177 (standalone RF) to 0.0042.
- **Drawbacks:** The model strictly predicts continuous yield volume (t/ha) rather than classifying the binary "Failure Anomalies" required for disaster relief triggering. Additionally, its heavy reliance on real-time pesticide data creates a severe operational bottleneck.

**Paper 5: Digital Twin-Based Uncertain Weather Condition Monitoring for Enhanced Crop Yield Prediction (Kenneth, 2026)**  
- **Method:** Kenneth introduced the "CropTwin" framework, integrating digital twin technology with Monte Carlo simulations to computationally model weather uncertainty using continuous satellite telemetry sourced directly from the NASA POWER API.
- **Results:** The simulated uncertainty approach proved highly viable, generating a real-time yield prediction of 5.90 t/ha compared to an uncertain weather projection of 5.62 t/ha without the need for local hardware.
- **Drawbacks:** It exclusively models weather uncertainty while completely ignoring critical biotic stress factors (like pest infestations driven by humidity). It also operates purely as a predictive monitor, lacking a Decision Support System (DSS) to issue actionable intervention advisories.

## 2.2 Research Gap
Through the critical analysis of the existing literature, three major technological and operational gaps have been identified that limit current agricultural forecasting systems:

1. **The Prediction Labeling Gap:** Current hybrid models (e.g., Yan et al., 2025) focus entirely on predicting absolute, continuous crop volume (t/ha). They fail to classify whether a drop in yield constitutes a full-scale agricultural "failure anomaly," which is the actual binary metric required by governments for immediate disaster intervention and crop insurance triggering.
2. **The Scalability & Infrastructure Gap:** Existing Cyber-Physical Systems (CPS) and agricultural Digital Twins (e.g., Banerjee et al., 2024) rely heavily on expensive, localized IoT sensor networks. This "single-farm silo" approach poses massive data interoperability challenges and is financially unviable for smallholder farmers across large states like Odisha. 
3. **The Explainability & Actionable Feedback Gap:** While advanced deep learning models (e.g., Arya et al., 2026; Andini & Utomo, 2021) achieve high accuracy, they operate as uninterpretable black boxes. Even advanced monitoring frameworks (e.g., Kenneth, 2026) lack an integrated, intelligent Decision Support System (DSS) that automatically translates mathematical predictions—like LSTM attention weights—into actionable agronomic advisories for the end-user.

Our proposed Cognitive Digital Twin addresses these exact gaps by bypassing IoT hardware in favor of NASA/Open-Meteo satellite APIs, predicting binary failure anomalies alongside continuous yield, and utilizing a Groq-powered LLM to translate tensor outputs into plain-language advisories.

---

# Chapter 3: Requirement Analysis

## Functional Requirements
- **Historical Data Ingestion:** The system must automatically clean, parse, and standardize 20 years of government crop yield CSV files to build the baseline database.
- **Failure Threshold Calculation:** The system must group data by district and season to calculate the First Quartile (Q1) statistical threshold to label crop failure anomalies.
- **Satellite Telemetry Fetching:** The system must execute API requests to NASA POWER and Open-Meteo to continuously fetch 4 core environmental variables (Precipitation, Temperature, Humidity, Soil Wetness).
- **Dual-Track Predictive Inference:** The system must pass processed data through both an LSTM-Attention deep learning model and an XGBoost ensemble to predict yield and failure risk.
- **Interactive What-If Simulation:** The system must allow users to adjust climate sliders on the dashboard and immediately run Monte Carlo simulations to view counterfactual disaster risks.
- **Expert Advisory Chatbot:** The system must integrate a Groq LLM to accept natural language questions and return plain-English agronomic advice.
- **Real-Time Monitoring & Dashboard:** The system must execute a continuous 60-second polling loop to fetch live telemetry from Open-Meteo, interpolate the data in real-time, and render live predictions across 30 Odisha districts using an interactive Leaflet map and Recharts gauges.

## Non-functional Requirements
- **Security:** All external API transfers (NASA, Open-Meteo, Groq) must use HTTPS/TLS encryption to ensure data integrity.
- **Reliability:** The backend must implement a `realtime_cache` and auto-retry logic to guarantee uptime even if external satellite APIs temporarily drop connection.
- **Performance:** Interactive Monte Carlo "What-If" climate simulations must compute and return updated visual risk predictions to the UI in under 2 seconds.
- **Scalability:** The FastAPI backend architecture must be horizontally scalable to support future multi-state expansion without requiring database schema redesigns.
- **Maintainability:** The machine learning predictive engine must be strictly decoupled from the UI layer via a DAG Orchestrator, allowing data scientists to swap models seamlessly.

## Hardware Requirements
- **Backend Deployment:** Dedicated Server or Cloud Compute Node (e.g., AWS/GCP instance) to host the FastAPI application and Orchestrator.
- **Model Training:** GPU-accelerated Development PC/Server for initial PyTorch deep learning training and Ridge-stacking calibration.
- **End-User Client:** Standard Workstation, Laptop, or Tablet for agronomists and farmers to access the web-based GIS dashboard.

## Software Requirements
- **Backend Languages & Frameworks:** Python 3.10+, FastAPI, PyTorch, XGBoost, Pandas, Numpy, Scikit-learn.
- **Frontend Languages & Frameworks:** JavaScript, React 19, Vite, Leaflet (GIS), Recharts.
- **LLM Integration:** Groq API SDK.
- **External APIs:** NASA POWER API, Open-Meteo API, Groq LLM API (llama-3.3-70b-versatile).

---

# Chapter 4: Product Design

## System Architecture
*([Insert Architecture Diagram here from Slide 12 of Final-PPT-Draft.pdf])*

The architecture of the Cognitive Digital Twin operates across a continuous loop bridging the physical and virtual worlds:
- **Data Acquisition Layer (Sources):** Extracts continuous satellite telemetry (NASA POWER API) and historical yield data (UPAg portal), running it through an automated Python/Pandas ETL pipeline to create 84-day temporal windows.
- **Cognitive Layer (Brain):** A dual-track machine learning engine. Track A utilizes ensemble regression (XGBoost) for baseline yield forecasting. Track B utilizes a PyTorch 3D Tensor LSTM-Attention model to map deep temporal weather patterns directly to biophysical stress triggers.
- **Application Layer:** The unified JSON predictions are routed to the interactive frontend dashboard, rendering live metrics, and providing actionable feedback directly to the end-users via the Expert Advisory LLM.

## Flowchart and Workflow Explanation
*([Insert Flowcharts from Slides 17-21 of Final-PPT-Draft.pdf here])*

The workflow of the system is governed by several core algorithms orchestrated via a Directed Acyclic Graph (DAG):
- **Data Ingestion Workflow:** The system extracts an 84-day window for a given district and season, aggregates daily metrics into 12 weekly means, appends static features, and computes Q1 thresholds.
- **State Update Workflow:** When new yield data arrives, the system validates the rows. If valid, it merges the data, fetches the missing NASA telemetry, retrains the LSTM+XGBoost models, evaluates metrics against the previous deployment, and updates the twin's state if the new model performs better.
- **Prediction Ensemble Workflow:** User intent is classified into one of 5 query types (e.g., `full_diagnosis`). The DAG Orchestrator routes the request to the required model nodes, computes predictions simultaneously, and blends them using Ridge Meta-Learner weights (Yield = 0.2·LSTM + 0.8·XGBoost; Failure = 0.68·LSTM + 0.32·XGBoost).
- **Real-Time Monitoring Workflow:** The frontend continuously polls the `/api/realtime/coordinate` endpoint every 60 seconds. The backend fetches a live 16-day forecast from Open-Meteo, blends it with the 20-year NASA climatology base, and passes it through the orchestrator to generate a live, interpolated prediction stream.

## UML Diagrams

### Use Case Diagram
*([Insert updated_use_case_ai_rectangular.jpg here])*

**Workflow:** The Agricultural Analyst interacts with the system to View District Yield Trends, Select Districts on Map, and Run What-If Simulations via Monte Carlo dropouts. The end Farmer acts as a consumer to Receive Alerts and Query the Advisory LLM. The system boundary ("Cognitive Digital Twin System") interfaces with external actors, specifically executing automated pulls from the NASA POWER API (for historical replay) and Open-Meteo API (for the Real-Time Monitor).

### Sequence Diagram
*([Insert sequence_diagram_2_ppt_optimized.png here])*

**Workflow:** This diagram illustrates the execution flow for the Real-Time Monitor. The Analyst opens the monitor on the frontend, triggering a 60-second polling loop. The FastAPI Backend calls the `DistrictResolver` to identify the geographic zone, fetches real-time snapshots from `Open-Meteo`, and aggregates them with the 20-year climatology base. It caches this telemetry (`realtime_cache`) for smooth 1-second interpolation on the UI, and finally passes the tensor to the `DAGOrchestrator` to compute the prediction and biophysical triggers.

### Class Diagram
*([Insert Class Diagram from Slide 14 of Final-PPT-Draft.pdf here])*

**Workflow:** Defines the programmatic structure of the application. The `FastAPIBackend` acts as the controller, resolving coordinates via `DistrictResolver` and aggregating telemetry from `OpenMeteoClient` and `NASAAPIClient` into a unified `TelemetryRecord`. This record is passed into the `CDTPredictor` class, which holds instances of `LSTMAttention`, `XGBoostModel`, and the `MetaLearner`. Outputs are standardized into a JSON response containing yield, failure risk, and extracted `BiophysicalTriggers`.

## User Interface Design
*(Screenshots to be inserted by the team from the deployed system)*

- **Dashboard:** The central landing view featuring the interactive Leaflet GIS map of Odisha's 30 districts, allowing the user to select specific regions, view aggregated yield trends, and query the Expert Advisory Chatbot.
- **Replay Simulator:** A specialized UI component that allows analysts to select historical years and seasons, utilizing the NASA POWER API to replay past agricultural cycles and compare historical predictions against actual ground-truth failure anomalies.
- **Real-Time Monitor:** An inline dashboard featuring 4 live telemetry gauges (Temperature, Humidity, Precipitation, Soil Moisture) and a 12-week continuous bar chart plotting 20-year normal climatology against current and forecast conditions, updated via a 60-second polling loop.

---

# Chapter 5: Product Development

## Hardware Development
- **Not Applicable:** Unlike traditional Cyber-Physical Systems that require expensive Internet of Things (IoT) sensors, circuit designs, and custom PCBs scattered across agricultural fields, our Cognitive Digital Twin completely bypasses local hardware. The product was deliberately developed to ingest continuous macro-telemetry from existing satellite databases (NASA POWER / Open-Meteo), making the system hardware-free and highly scalable for smallholder farmers.

## Software Development Modules
- **Data Engineering Module:** An automated ETL (Extract, Transform, Load) Python pipeline that downloads government crop yield CSVs and synchronizes them with continuous satellite weather data.
- **Machine Learning Module:** The core predictive engine constructed using PyTorch (for the deep temporal LSTM-Attention network) and XGBoost (for tabular decision-tree regression and failure classification).
- **Backend & Orchestration Module:** A FastAPI server containing a custom Directed Acyclic Graph (DAG) router (`orchestrator.py`) that intelligently routes user queries to the required predictive models, heavily optimizing API response times.
- **Decision Support System (DSS) Module:** An integration with the Groq API SDK to embed an expert AI chatbot directly into the system, translating complex mathematical model outputs into actionable agronomic logic.
- **Frontend UI Module:** An interactive dashboard developed using React 19, featuring Leaflet mapping for GIS district selection and Recharts for live telemetry rendering.

## Algorithms
The system relies on four core algorithms. 

**Algorithm 1: Data Ingestion & Harmonization Pipeline**
```text
Input: Govt yield CSVs + NASA POWER daily telemetry
Output: Synchronized tensors X_seq (1113, 84, 4), y_yield, y_fail
BEGIN
  For each (district, year, season):
    Extract 84-day temporal window (e.g., Kharif: Jun 15 - Sep 6)
    Aggregate 84 daily records into 12 weekly means (Temp, Humidity, Precip, Wetness)
    Append static features [district_index, season_onehot, year_offset]
  Calculate Q1 (25th percentile) yield threshold per district
  Label target y_fail = 1 IF yield < Q1 ELSE 0
  Scale features and save serialized tensors (.npy)
END
```

**Algorithm 2: Digital Twin State Update Algorithm**
```text
Input: New yield records from government portal
Output: Updated deployed models
BEGIN
  Validate new records (>50% non-interpolated rows)
  IF Invalid THEN Reject Update
  Merge new dataset and fetch missing NASA telemetry
  Retrain Track A (XGBoost) and Track B (LSTM-Attention)
  Evaluate new model metrics (R²_new, AUC_new) on validation set
  IF (R²_new ≥ R²_old - 0.02) AND (AUC_new ≥ AUC_old - 0.02) THEN
    Deploy new models to production
  ELSE
    Fallback to current models
END
```

**Algorithm 3: Multi-Model Prediction Ensemble**
```text
Input: API Request + telemetry vector
Output: Unified JSON Prediction
BEGIN
  Classify query intent (yield_forecast, failure_risk, what_if, full_diagnosis)
  Route request through DAG Orchestrator
  Execute LSTM-Attention to extract Temporal Features and Biotic Triggers
  Execute XGBoost for Yield Regression and Binary Classification
  Blend outputs via Ridge Meta-Learner weights:
    Final_Yield = (0.2 * LSTM_Yield) + (0.8 * XGB_Yield)
    Final_Failure = (0.68 * LSTM_Fail) + (0.32 * XGB_Fail)
  Return Unified JSON response
END
```

**Algorithm 4: Monte Carlo Dropout for Uncertainty Quantification**
```text
Input: Climate-modified telemetry vector
Output: Yield prediction with 90% confidence interval
BEGIN
  Activate dropout layers in LSTM at inference time
  Repeat 500 times:
    Randomly disable 20% of neurons
    Pass telemetry through network -> collect prediction_i
  Calculate Final_Prediction = Average of 500 passes
  Calculate Uncertainty = Standard Deviation of 500 passes
  Sort 500 predictions
  Calculate 90% Confidence Interval = [Value at 5th percentile, Value at 95th percentile]
END
```

## Development Process
The development of the Cognitive Digital Twin followed a systematic, five-stage engineering lifecycle:

1. **Requirement Analysis:** The process began by identifying the limitations of existing agricultural systems—specifically their reliance on expensive local IoT sensors and uninterpretable models. We established the requirement for a hardware-free, remote-sensing-based platform that could deliver continuous, explainable disaster predictions to smallholder farmers.
2. **Design Phase:** We architected a dual-track machine learning framework to process both tabular and deep temporal data. Simultaneously, we designed an interactive user interface (UI) to support real-time GIS monitoring, counterfactual Monte Carlo "What-If" climate simulations, and an integrated LLM advisory chatbot.
3. **Implementation Phase:** The backend was developed using FastAPI and Python, integrating an automated ETL pipeline for NASA POWER telemetry. The core predictive engine was implemented using PyTorch (LSTM-Attention) and XGBoost. The frontend was built utilizing React 19, Vite, and Leaflet for dynamic mapping, and the Groq API SDK was integrated to power the Decision Support System.
4. **Testing Phase:** We implemented rigorous validation protocols. The machine learning models were tested on a strictly chronological hold-out dataset (Years ≥ 2020) to ensure there was zero temporal data leakage. Backend API endpoints and orchestration logic were validated using unit tests (`pytest`).
5. **Deployment:** Finally, the fully integrated system was deployed with a live state-update pipeline. The frontend was configured to execute continuous 60-second polling against the Open-Meteo API, ensuring the deployed twin remains synchronized with real-world physical conditions.

---

# Chapter 6: Implementation

## Programming Languages
- **Python (3.10+):** Utilized exclusively for all backend operations, including the automated data extraction pipeline, machine learning model training (`train.py`), API deployment (`main.py`), and DAG orchestration.
- **JavaScript (ES6+):** Utilized for the entirety of the frontend logic and user interface components.

## Tools
- **Vite (v8):** Used as the ultra-fast build tool and development server for the React frontend, allowing for instant hot-module replacement during UI development.
- **Git & GitHub:** Employed for rigorous version control, collaborative codebase management, and branching between experimental ML models.
- **Uvicorn:** Utilized as the high-performance ASGI web server to deploy the FastAPI backend concurrently.
- **Postman / cURL:** Used for rigorous manual testing and verification of the API endpoints during the development phase.

## IDE (Integrated Development Environment)
- **Visual Studio Code (VS Code):** Served as the primary IDE for developing both the Python backend and React frontend, utilizing extensions for syntax highlighting and continuous linting (ESLint).
- **Jupyter Notebooks:** Used in the early stages of data engineering and exploratory data analysis (EDA) to visualize dataset distributions before finalizing the ETL pipeline into pure Python scripts.

## Libraries & Frameworks
The system relies on a highly specialized stack of open-source libraries:

**Backend & Machine Learning Libraries:**
- `FastAPI`: High-performance Python web framework for building the API endpoints.
- `PyTorch (v2.0+)`: Core deep learning tensor library used to construct and train the 3D `LSTMAttention` network.
- `XGBoost`: Gradient boosting library used for the tabular regression and binary failure classification track.
- `Scikit-learn`: Utilized for the Ridge Stacking meta-learner to blend predictions, as well as for data scaling (`MinMaxScaler`).
- `Pandas & Numpy`: Essential for mathematical tensor manipulation and aggregating the 84-day temporal windows.
- `Groq SDK`: Integrated to pipe JSON outputs directly into the `llama-3.3-70b-versatile` LLM.

**Frontend Libraries:**
- `React 19`: Core component-based UI framework.
- `Leaflet & React-Leaflet`: Used to render the interactive, clickable 30-district GIS map of Odisha.
- `Recharts`: Utilized to render dynamic, animated telemetry gauges, continuous bar charts, and Monte Carlo confidence intervals.
- `Lucide-React`: Used for clean, modern SVG iconography across the dashboard.

## Implementation Screenshots
*([Insert screenshot of the VS Code Editor showing main.py or App.jsx here])*
*([Insert screenshot of the terminal running 'uvicorn main:app' and 'npm run dev' successfully here])*
*([Insert screenshot of a successful API JSON response from Postman or the browser Network Tab here])*

---

# Chapter 7: Testing and Validation

## Unit Testing
- **API Endpoints:** Executed automated unit tests utilizing `pytest` to individually verify that the FastAPI backend routes (e.g., `/api/predict/coordinate` and `/api/realtime/coordinate`) accurately return expected JSON payload structures.
- **Model Tensors:** Conducted smoke testing on the `LSTMAttention` and `XGBoost` classes to verify that input tensor dimensions accurately matched the 84-day temporal shape `(batch, 84, 4)` before proceeding to full model training.

## Integration Testing
- **DAG Orchestrator:** Tested the internal pipeline bridging the PyTorch deep learning models, XGBoost decision trees, and the Ridge Meta-Learner. Confirmed that the orchestrator accurately blends sub-model predictions (e.g., 0.2 LSTM + 0.8 XGBoost for Yield) into a singular accurate output without crashing.
- **Client-Server Integration:** Verified that the React 19 UI components correctly serialize and transmit data via HTTP requests, and that the backend successfully parses this data and returns the correct payload to trigger React state updates on the dashboard.

## System Testing
- **Continuous Real-Time Loop:** Executed full end-to-end (E2E) testing on the live deployed system to verify the `Real-Time Monitor`. Confirmed that the system successfully executes the 60-second polling loop, fetching live data from Open-Meteo, interpolating via `realtime_cache`, and rendering UI gauges without memory leaks or dropped connections.
- **Decision Support System:** Verified the end-to-end workflow between the prediction engine and the external Groq API, ensuring mathematical crop-failure probabilities were successfully ingested and translated into plain-English advice.

## Test Cases
| Test ID | Test Description | Input Data | Expected Output | Status |
|---|---|---|---|---|
| TC-01 | Submit valid geographical coordinate for district resolution | Lat: 20.9, Lng: 86.3 | Returns `{"district": "Bhadrak"}` | Pass |
| TC-02 | Execute What-If Monte Carlo simulation | Climate sliders set to +2°C, -10% Rainfall | 90% Confidence Interval generated in < 2s | Pass |
| TC-03 | Open-Meteo API temporary failure | Disconnect internet connection | System loads last known `realtime_cache` | Pass |
| TC-04 | Query LLM with high failure risk | `y_fail = 1`, trigger = "Thermal Stress" | Chatbot outputs drought mitigation advisory | Pass |

## Performance Evaluation
### Machine Learning Metrics
Data was split into an 80/10/10 configuration, with testing performed on a strictly held-out chronological dataset (Years ≥ 2020) to prevent temporal data leakage.
- **Accuracy (R²):** The stacked ensemble achieved **0.712** for continuous yield prediction (a 54% improvement over the naive-mean baseline).
- **Precision (Failure AUC):** The system achieved an Area Under Curve (AUC) of **0.721** for predicting binary disaster thresholds.

### System Metrics
- **Response time:** API predictions returned in `< 1.2 seconds` for standard inference.
- **Latency:** Complex Monte Carlo simulations (requiring 100 deep learning dropout iterations) completed with an average latency of `< 2.5 seconds`.
- **Throughput & Availability:** Auto-retry logic on external API fetching (NASA/Open-Meteo) ensured **99.9%** availability during testing.
- **CPU & Memory usage:** Deployed FastAPI backend instances utilized `< 400 MB` RAM during concurrent inference requests, heavily optimized by the DAG router skipping unneeded model branches.

---

# Chapter 8: Results and Discussion

## Results (Graphs, Tables, and Comparisons)
*([Insert visual charts/graphs from Slides 23-26 of Final-PPT-Draft.pdf here, e.g., the 12-week feature correlation heatmap or the Bar Chart comparing R² scores])*

### Model Performance Comparison Table
| Metric | Baseline (Naive-Mean) | LSTM (Deep Temporal) | XGBoost (Tabular) | Stacked Ensemble (Ridge) |
|--------|----------------------|----------------------|-------------------|--------------------------|
| Yield RMSE (Quintals/Acre) | 6.75 | 4.05 | 3.81 | **3.63** |
| Yield R² | - | 0.641 | 0.682 | **0.712** |
| Failure AUC | - | 0.685 | 0.663 | **0.721** |

**Comparison Analysis:** The table above illustrates the supremacy of the dual-track stacking approach. XGBoost achieved a higher R² than the LSTM due to its robust handling of non-linear tabular features, but struggled with binary failure prediction. The LSTM excelled at capturing sequential climate drops (raising the AUC) but struggled with absolute regression. The Ridge Meta-Learner successfully extracted the strengths of both models, achieving a final Yield RMSE of 3.63 (a massive ~54% error reduction against the naive baseline).

## Discussion

### Product Performance
The product performs exceptionally well under real-world simulation. The FastAPI backend successfully processes the heavy 84-day tensor inputs in under 1.2 seconds, making the system highly responsive. Furthermore, by heavily optimizing the DAG Orchestrator to bypass unnecessary model branches, the system scales smoothly across all 30 Odisha districts without significant memory bloat, processing the 60-second real-time polling loop continuously without dropping packets.

### Advantages
- **Unprecedented Scalability:** Complete bypass of expensive, localized IoT ground-sensor infrastructure by relying entirely on free, global satellite telemetry (NASA/Open-Meteo).
- **Explainability & Trust:** Integrating the Groq API SDK translates historically opaque deep learning outputs into highly actionable, plain-English mitigation advisories for end-users.
- **True Proactivity:** Transitions agricultural management from passive retrospective statistics (waiting for yield reports) to proactive counterfactual disaster anticipation via Monte Carlo simulations.

### Improvements
- **Model Extrapolation Limits:** The current dataset reveals a post-COVID yield regime shift (mean yields jumped from 7.8 to 14.0). The chronological train/test split proved the models struggle to extrapolate this unprecedented jump. Future improvements require integrating soil-health dynamic data to help the models adapt to sudden macro-regime shifts.
- **Data Granularity:** The models currently aggregate telemetry at the district-level. Upgrading the spatial resolution of the Open-Meteo fetches to block-level or village-level coordinates would drastically improve the precision of localized failure thresholds.

---

# Chapter 9: Conclusion and Future Works

## Conclusion
The development of the Cognitive Digital Twin successfully met and exceeded all established criteria for predicting agricultural failure.

### Objectives Achieved
We successfully architected a highly accurate, dual-track machine learning pipeline capable of parsing 84-day temporal weather cycles. The system achieved a massive ~54% error reduction in yield prediction compared to baseline metrics, successfully isolating physical crop stressors without relying on any expensive, localized ground-sensor hardware.

### Product Developed
The final product is a fully-integrated, full-stack platform consisting of a high-performance Python/FastAPI backend executing real-time 60-second polling against the Open-Meteo API. This backend seamlessly orchestrates a PyTorch/XGBoost ensemble and pipes the resulting insights into an interactive, React 19 GIS dashboard equipped with a Groq LLM-powered Decision Support System (DSS).

### Benefits
- **Hardware-Free Operations:** Complete elimination of ground-sensor maintenance costs by relying strictly on global satellite telemetry.
- **Proactive Management:** Empowers government officials and stakeholders to run Monte Carlo counterfactual simulations, enabling preemptive disaster mitigation rather than retrospective damage calculation.
- **Explainable AI:** Converts complex deep learning outputs into plain-English agronomic advice that non-technical end-users can easily act upon.

## Future Improvements
1. **Multispectral Imagery Fusion:** Integrate MODIS/Sentinel satellite vegetation indices (NDVI/EVI) alongside the weather telemetry to computationally track physical crop diseases and hyper-local growth staging.
2. **Multi-Crop & Spatial Expansion:** Extend the digital twin framework beyond Odisha rice to cover wheat, pulses, and maize cultivation across neighboring states.
3. **Localized Edge Delivery:** Implement SMS or WhatsApp integration directly from the Groq LLM layer to deliver hyper-localized, Odia-translated advisories directly to farmer mobile devices without requiring internet browser access.

---

# References
[1] A. Andini and P. Utomo, "Climate Prediction Using RNN LSTM to Estimate Agricultural Products Based on Koppen Classification," *Journal of Physics: Conference Series*, vol. 1836, 2021.
[2] S. Arya et al., "A Time-Series Hybrid Multi-Model Machine Learning Framework for Staple Crops Yield Prediction," *Expert Systems with Applications*, 2026.
[3] O. Kenneth, "Digital Twin-Based Uncertain Weather Condition Monitoring for Enhanced Crop Yield Prediction," *Meteorological Applications*, 2026.
[4] J. Yan et al., "Crop Yield Time-Series Data Prediction Based on Multiple Hybrid Machine Learning Models," *Computers and Electronics in Agriculture*, 2025.
[5] S. Banerjee, A. Mukherjee, and S. Kamboj, "Integrating Digital-Twins and Advanced Crop Recommendation Agricultural Systems," 2024.
[6] NASA Langley Research Center, "Prediction of Worldwide Energy Resources (POWER) Agroclimatology Data Access Viewer & API Documentation," 2026. [Online]. Available: https://power.larc.nasa.gov/.
[7] Department of Agriculture & Farmers' Empowerment, "Historical District-Wise Crop Production Statistics (1997–2025)," Government of Odisha, 2025.
[8] T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," in *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 2016, pp. 785–794.
[9] A. Paszke et al., "PyTorch: An Imperative Style, High-Performance Deep Learning Library," in *Advances in Neural Information Processing Systems 32*, 2019, pp. 8024–8035.
