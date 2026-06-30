# Wiki Log

Chronological record of all activities in the Digital Twin project.

## [2026-06-20] Frontend Initialization & Component Architecture
- Initialized Vite + React project inside the `frontend/` directory.
- Installed frontend dependencies: `leaflet`, `react-leaflet`, `recharts`, and `lucide-react`.
- Implemented core Vanilla CSS stylesheet `frontend/src/index.css` defining the dark glassmorphism theme using CSS variables.
- Developed core interactive components:
  - `OdishaSVGMap`: Stylized interactive SVG map of Odisha's 30 districts with status-based choropleth fills and tooltips.
  - `OdishaGISMap`: Leaflet-based coordinate-aware satellite map utilizing dark-themed tiles and reactive marker overlays.
  - `MapCard`: Dual-mode wrapper with toggle logic for SVG vector and GIS coordinate views.
  - `MetricsCard`: Display container for yield forecasts, failure anomaly probability, active stressors, and confidence bands.
  - `Timeline`: Synchronized Recharts area charts for precipitation, soil wetness, temperature, and humidity with a 12-week range slider.
  - `Heatmap`: Explainable AI representation of LSTM attention weights mapping peak weight steps to biophysical stress thresholds.
  - `DSSChat`: Conversational sidebar panel simulating a natural language interface to the CDT expert advisory node.
- Created `backend/requirements.txt` listing packages and implemented a FastAPI backend `backend/main.py` serving telemetry, historical yield indices, predictions, and counterfactual weather simulations.
- Updated `wiki/index.md` to reference the newly implemented files.

## [2026-06-19] Architecture Finalization | Cognitive Digital Twin
- Finalized the project architecture as a **4-layer Cognitive Digital Twin (CDT)**, replacing the earlier "Cyber-Physical Digital Twin (CPDT)" terminology.
- **Layer 1 — Physical Entity Layer**: Farmers, fields, rice crop, climate system, 30 districts, agronomic practices.
- **Layer 2 — Data Acquisition Layer**: Hybrid data collection (govt. statistics + NASA POWER API).
- **Layer 3 — Cognitive Analytics Layer**: Dual-track ML/DL prediction engine, failure detection with biophysical triggers, Monte Carlo + What-If simulation engine.
- **Layer 4 — Orchestration & Application Layer**: LangGraph DAG with guardrails, Agentic Decision Support System (DSS) with tool access, interactive dashboard with simulation sliders, SVG/GIS map toggle.
- Defined 3 feedback loops: Information Flow (↑), Action & Decision Flow (↓), Direct Farmer Interaction (↔).
- Rewrote [[Cognitive Digital Twin — Architecture]] wiki page with full 4-layer specification.
- Updated all concept pages ([[LSTM-Attention Model]], [[Failure Logic]], [[NASA POWER Integration]], [[Yield Data Harmonization]]) to reference CDT and their respective architecture layers.
- Generated architecture diagram and detailed specification in `not-necessary/` for reference.

## [2026-06-18] Presentation & Project Documentation
- Created 12-slide Marp presentation deck for the research internship.
- Created project abstract and objectives document (`sources/data/project_abstract.md`) with clearly separated Problem Statement and Objectives.
- Created frontend architecture plan (`frontend-plan/frontend_architecture_plan.md`).

## [2026-06-17] Data Harmonization, Telemetry Ingestion, & Failure Research
- Harmonized historical `odisha_data.csv` (1997-2019) with recent `DES-District-Data-For-2024-25.csv` (2024-25) Rice yields via [harmonize_yield.py](../code/harmonize_yield.py).
- Applied linear interpolation to fill the 2020-2023 and 2025 temporal gaps.
- Converted yield units to Quintals/Acre and calculated district-season specific $Q_1$ thresholds.
- Created [fetch_nasa_telemetry.py](../code/fetch_nasa_telemetry.py) and successfully fetched daily weather data for all 30 districts from 2006-01-01 to 2026-05-31.
- Created [merge_telemetry_yield.py](../code/merge_telemetry_yield.py) to extract 12-week vegetative cycles, aggregate daily climate data into weekly features, and merge them.
- Verified [final_dataset.csv](../sources/data/final_dataset.csv) contains 1,200 rows and 58 columns with zero missing values. (Later refined to 1,087 rows after removing interpolated 2025 data.)
- Installed `pypdf` and conducted research on biophysical failure triggers using local PDFs.
- Created [[Failure Logic]] documenting four core climate-induced stress states (Drought, Heat Sterility, Pest/Blast Risk, Submergence Flooding) and their thresholds.
- Updated [[Yield Data Harmonization]], created [[NASA POWER Integration]], and updated [[Odisha Pilot]] (linked to [[odisha]]).

## [2026-06-17] Data Engineering | Yield & Telemetry
- Verified Odisha district yield data availability (1970-2020).
- Identified temporal gap for **2020-2024**; plan to scrape UPAg/DESAgri.
- Created `code/nasa_power_ingest.py` for automated climate telemetry.
- Defined unit conversion requirements (MT/ha to Q/Acre).

## [2026-06-25] Model Overhaul | Track-A/Track-B Replaced
- Evaluated all modeling approaches comprehensively: Track-A (RF weather-only), Track-B (LSTM-Attention), XGBoost, Enhanced XGBoost, and Deep NN with MC Dropout.
- Track-B LSTM-Attention removed after benchmarking showed R²=0.048 (effectively random) and F1=0.00 (never identified a failure).
- Weather features alone have very low correlation with yield (max r=0.16) — the key insight driving the architecture change.
- New feature engineering: expanded from 48 weather-only to 72 features (added District, Season, Year, aggregated stats, critical period features, interactions).
- New dual-model pipeline: XGBoost (primary, fast inference) + Deep NN with MC Dropout (secondary, uncertainty quantification).
- MC Dropout provides principled Bayesian uncertainty at zero extra cost — replaces manual N=100 Monte Carlo approach with N=500 dropout-enabled forward passes.
- Created `/code/phase-2-training/` with clean pipeline: `prepare_data.py` → `train.py` → `predict.py`.
- Updated [[Prediction Engine: Dual-Model Ensemble]] (formerly [[LSTM-Attention Model]]), [[Cognitive Digital Twin — Architecture]], [[Comparative Analysis-2026]] to reflect new architecture.

## [2026-06-16] Ingestion | CDT Project Specification
- Ingested core technical spec for "Odisha Pilot Engine".
- Created concept pages: [[Cognitive Digital Twin — Architecture]], [[LSTM-Attention Model]].
- Created entity page: [[Odisha Pilot]].
- Defined 3D Tensor geometry (1200 × 12 × 4) and failure logic ($Q_1$ thresholding).

