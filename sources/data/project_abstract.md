# Project: Cyber-Physical Digital Twin for Smart Agriculture

---

## Abstract

Regional agricultural forecasting in India continues to rely on static, retrospective statistical reports that are published months after the crop season concludes. These reports offer no predictive capability and provide no early warning mechanism for climate-induced crop failures. Meanwhile, the growing volatility of monsoon patterns, rising temperatures, and shifting pest vectors have made crop losses increasingly frequent and severe—particularly in vulnerable states like Odisha, where rice cultivation across 30 districts sustains millions of smallholder farming households.

This project proposes the development of a **Cyber-Physical Digital Twin (CPDT)** framework that replaces passive statistical reporting with an active, continuous, data-driven prediction engine. The framework constructs a virtual replica of Odisha's agricultural landscape by synchronizing a 20-year harmonized crop yield dataset (2006–2025) with daily environmental telemetry sourced from the NASA POWER API. The telemetry captures four critical climate variables—precipitation, temperature, relative humidity, and root zone soil wetness—aggregated into 12-week vegetative cycle tensors aligned to the Kharif and Rabi cropping seasons.

The predictive core employs a dual-track cognitive analytics architecture. **Track A** utilizes a weighted ensemble of Random Forest and XGBoost regressors operating on flattened seasonal statistics to establish a stable tabular baseline. **Track B** deploys a Stacked Long Short-Term Memory (LSTM) network with a Temporal Attention mechanism that processes the sequential 12-week weather tensors as a 3D input array of shape (1200 × 12 × 4), enabling the model to learn recurrent temporal dependencies and isolate the specific calendar weeks where environmental stress triggers crop failure. A Monte Carlo simulation layer quantifies prediction uncertainty under volatile climate scenarios.

Crop failure is formally defined using a statistical first-quartile ($Q_1$) thresholding logic computed per district and season, transforming continuous yield regression into a binary anomaly classification task. Biophysical stress triggers—drought, thermal sterility, pest outbreak risk, and submergence flooding—are mapped from the climate telemetry features to the attention weight outputs, enabling Explainable AI (XAI) advisories that connect mathematical predictions to actionable agronomic guidance.

The entire pipeline is orchestrated through a LangGraph Directed Acyclic Graph (DAG) state machine comprising Ingestion, Execution, and Expert Advisory nodes, with hard numerical guardrails that prevent the advisory LLM from generating recommendations until model outputs are validated in the shared graph state.

---

## Problem Statement

Current agricultural yield estimation for the state of Odisha relies on post-season government statistical reports that are:

1. **Retrospective**: Published after the harvest season has concluded, offering zero predictive or early-warning value to farmers, administrators, or disaster relief agencies.
2. **Temporally Fragmented**: Historical yield records (1997–2019) and recent advance estimates (2024–2025) exist in separate, incompatible datasets with inconsistent district naming conventions, differing unit systems (Tonnes/Hectare vs. Kg/Hectare), and a complete data void for the period 2020–2023.
3. **Climatically Disconnected**: Yield statistics are recorded in isolation from the environmental conditions that caused them. There is no systematic linkage between weekly weather patterns during the vegetative growth cycle and the resulting harvest outcomes.
4. **Unexplainable**: Existing ML-based crop prediction models in the literature operate as black boxes—they output a yield number but cannot explain *which specific week* of the growing season, or *which specific climate variable*, triggered a yield deviation or crop failure.
5. **Regionally Coarse**: National and state-level models fail to capture the micro-climatic diversity across Odisha's 30 administrative districts, where coastal districts experience cyclonic flooding while western districts face drought stress within the same season.

There is no existing system that combines harmonized historical crop statistics, real-time satellite-derived environmental telemetry, sequential deep learning, and explainable advisory generation into a unified, continuously updating digital twin for district-level crop failure prediction in Odisha.

---

## Objectives

1. **Harmonize a 20-Year Crop Yield Dataset**: Merge and clean heterogeneous government crop statistics (1997–2019 historical records and 2024–2025 advance estimates) into a unified, continuous, district-stratified dataset covering 30 districts across 20 crop years (2006–2025) and 2 seasons (Kharif, Rabi), resolving naming inconsistencies, unit mismatches, and temporal data gaps through linear interpolation.

2. **Automate Environmental Telemetry Ingestion**: Build an automated pipeline to fetch, cache, and process daily climate telemetry (Precipitation, Temperature, Relative Humidity, Root Zone Soil Wetness) from the NASA POWER API for all 30 district centroids, and aggregate them into 12-week vegetative cycle feature vectors aligned to crop season calendars.

3. **Train a Dual-Track Predictive Engine**: Develop and evaluate two parallel modeling tracks—a tabular ensemble baseline (Random Forest + XGBoost) and a sequential deep learning model (Stacked LSTM with Temporal Attention)—for joint continuous yield regression and binary crop failure classification.

4. **Define and Validate Biophysical Failure Triggers**: Establish scientifically grounded, threshold-based rules for four climate-induced crop stress categories (Drought, Thermal Sterility, Pest/Pathogen Outbreak Risk, and Submergence Flooding) and validate them against LSTM attention weight distributions to ensure model explainability.

5. **Orchestrate a Guarded Advisory Pipeline**: Implement a LangGraph DAG state machine that sequences data ingestion, model execution, and LLM-based expert advisory generation with hard numerical guardrails preventing hallucinated recommendations.

6. **Deliver an Interactive Digital Twin Dashboard**: Design and build a responsive web interface featuring a dual-mode GIS/SVG interactive map of Odisha, a 12-week temporal slider, real-time attention heatmaps, Monte Carlo uncertainty visualizations, and natural language advisory alerts.
