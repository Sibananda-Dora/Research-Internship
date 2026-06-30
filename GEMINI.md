# GEMINI.md - Digital Twin Wiki Schema

This document defines the architecture and operational standards for the "Digital Twin: Crop Yield and Failure Prediction" project.

## 1. Architecture

### Raw Sources (`/sources`)
- Immutable source documents: research papers (PDF/MD), datasets (CSV/JSON), and model specs.
- Subdirectories: `/sources/papers`, `/sources/data`, `/sources/models`.

### The Wiki (`/wiki`)
- Persistent, interlinked knowledge base.
- Subdirectories:
    - `/wiki/entities`: Pages for specific crops, regions, or sensors.
    - `/wiki/concepts`: ML/DL architectures, failure modes (drought, pests), and Digital Twin theory.
    - `/wiki/analysis`: Comparative studies and synthesis of multiple sources.
    - `/wiki/sources`: Summaries of each individual source in `/sources`.

### The Code (`/code`)
- `/code/phase-2-training/` — Training pipeline for the prediction engine:
  - `prepare_data.py`: Feature engineering (72 features: 48 weather + 24 meta)
  - `train.py`: Trains XGBoost (primary) + Deep NN MC Dropout (secondary)
  - `predict.py`: `CDTPredictor` class with `.predict()` and `.monte_carlo()` methods
  - `models/`: Trained model artifacts (xgb_regressor.json, xgb_classifier.json, dnn_mc_dropout.pth)
  - `prepared_data/`: Preprocessed numpy arrays + scalers/encoders

## 2. Operational Workflows

### Ingest Workflow
1. **Read**: Analyze the new file in `/sources`.
2. **Summarize**: Create a new page in `/wiki/sources/`.
3. **Integrate**: 
    - Update or create relevant pages in `/wiki/entities` and `/wiki/concepts`.
    - Note contradictions or reinforcements of existing data.
4. **Log**: Append entry to `/wiki/log.md`.
5. **Index**: Update `/wiki/index.md`.

### Query Workflow
1. Consult `/wiki/index.md` to find relevant pages.
2. Synthesize answer from wiki pages.
3. If a new insight is discovered, file it back into `/wiki/analysis/`.

### Training Workflow
1. `prepare_data.py` — loads `final_dataset.csv`, engineers 72 features, scales, splits 80/20
2. `train.py` — trains XGBoost regressor+classifier and Deep NN with MC Dropout
3. `predict.py` — `CDTPredictor` ensemble with 500-sample MC Dropout for uncertainty

## 3. Formatting Standards
- Use **Wikilinks** (`[[Page Name]]`) for all cross-references.
- Every wiki page must have a `## Sources` section at the bottom.
- Use Mermaid diagrams for architecture and process flows.
- Maintain a consistent YAML frontmatter for status (e.g., `status: draft`, `status: verified`).

## 4. Current Objectives
- [x] Build the foundation for Crop Yield Prediction models (ML/DL).
- [x] Research failure mode triggers in Digital Twin simulations.
- [x] Replace Track-A/Track-B with XGBoost + Deep NN MC Dropout ensemble.
- [x] Engineer 72-feature space (48 weather + 24 meta features).
- [x] Implement MC Dropout for principled Bayesian uncertainty.
- [ ] Integrate trained models into FastAPI backend (`backend/main.py`).
- [ ] Implement Agentic AI logic for automated wiki maintenance.
- [x] Harmonize 20-year APY dataset (Merge historical with 2020-2024 recent data).
- [x] Automate NASA POWER 12-week tensor ingestion.
