# Project Current State

## Goal
Build a cognitive digital twin for Odisha rice yield prediction and crop failure early warning. Routes queries through a custom Python DAG orchestrator to LSTM, XGBoost, and stacking meta-learner nodes.

## Data
- **final_dataset.csv**: 1,083 clean rows, 30 districts, 2006–2024, 58 columns, **zero interpolated rows**.
- **Telemetry CSVs**: 30 daily files, 16,587 rows each (1981–2026 NASA POWER data).
- **Pretrain data**: 2,700 unlabeled 84-step daily sequences (30 districts × 45 years × 2 seasons).
- **Rabi window**: Nov 1–Jan 23 (consistent across all features).

## Model Architecture

### LSTM + Temporal Attention
- **Input**: 84-step daily sequences (84 × 4 variables) + 4-dim raw static → `nn.Embedding(30, 8)` expands district index to 8-dim → 11-dim effective static
- **Architecture**: 2-layer LSTM (64 hidden) with LayerNorm + learned positional bias + Temporal Attention
- **Params**: ~56.6K total
- **Initialization**: Pretrained encoder from masked autoencoder
- **Training**: Multi-task, graduated unfreezing, chronological validation holdout
- **Performance**: Yield R² **0.636**, Failure AUC **0.782**

### XGBoost
- **Input**: 23-dim features + meta-features (district, season, year as absolute offset)
- **Performance**: Yield R² **0.736**, Failure AUC **0.801**

### Stacking Meta-Learner
- Calibrated on held-out validation set (87 samples) — no test leakage
- Yield: **LSTM=0%, XGB=100%** (R²: **0.736**), Failure **LSTM=68%, XGB=32%** (AUC: **0.814**)

### Notable Changes (this session)
1. **Stacking calibration — no test leakage**: Uses held-out validation set instead of test set for blending weights.
2. **Chronological stacking**: Validation is a random 10% holdout from training; test set kept untouched for final evaluation.
3. **LSTM attention fix**: Added LayerNorm before attention scores + learnable positional bias `pos_bias` to reduce recency bias.
4. **Year encoding**: Changed from normalized `[0,1]` to absolute offset `year - 2006`. This lets the model learn a linear trend that extrapolates to future years.
5. **Cold-start districts**: Now raise `ValueError` with list of valid districts instead of silently defaulting to Angul.
6. **Confidence intervals in predict()**: Uses heuristic spread between LSTM and XGBoost predictions instead of hardcoded zeros.
7. **Orchestrator code smell**: Replaced `__import__('torch')` with clean `import torch`.
8. **Temporal generalization investigation**: Paper exercise (2022+ cutoff) revealed model can't extrapolate to post-COVID era (yield mean doubled from 7.8 to 14.0). Documented as known limitation.

## File Structure
- `code/phase-2-training/` — Main pipeline (prepare_data → train → predict → orchestrator)
- `code/phase-2-training/pretrain_autoencoder.py` — Masked autoencoder pretraining
- `code/phase-2-training/prepare_pretrain_data.py` — Extracts 84-step sequences for pretraining
- `code/harmonize_yield.py` — Yield data harmonization
- `code/fetch_nasa_telemetry.py` — NASA POWER ingestion 1981–2026
- `code/merge_telemetry_yield.py` — Merge telemetry with yields
- `code/apply_real_data_split.py` — Apply real rice data split
- `backend/main.py` — FastAPI serving all endpoints through orchestrator
- `models/` — Saved weights: `autoencoder_complete.pt`, `lstm_final.pth`, `xgb_regressor.json`, `xgb_classifier.json`, `meta_yield.pkl`, `meta_fail.pkl`
- `web/` — Static frontend (old hardcoded model, doesn't call real API)
- `wiki/` — Documentation
- `CURRENT_STATE.md` — This file

## Known Issues
1. **Attention still peaks at week 12**: LayerNorm + pos_bias didn't fully solve recency bias. The 87-sample validation set may be too small to calibrate the positional bias. More epochs or stronger initial bias may help.
2. **Rabi failure rate validation low (11%)**: The chronological validation set has fewer failure events, making failure calibration less reliable.
3. **web/ frontend**: Uses old hardcoded model logic instead of calling backend API.
4. **Temporal generalization limited**: Model trained on 2006–2021 cannot predict post-COVID yield surge (mean 7.8→14.0). Only weather features used; socio-economic shocks are outside scope.
5. **MC dropout std = 0 for yield**: Stacking weights yield=100% XGBoost, which is deterministic. Only failure probability benefits from LSTM uncertainty.

## Next Steps
1. Point `web/` frontend at the real backend API
2. Investigate stronger positional attention bias initialization to shift focus to weeks 4–8
3. Consider adding remote sensing features (NDVI, VHI) for better temporal generalization
