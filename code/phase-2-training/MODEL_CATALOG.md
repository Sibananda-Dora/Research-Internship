# CPDT Model Pipeline — Reference

File location: `code/phase-2-training/`

## Architecture Overview

```
Input (48-dim weather vector)
        │
        ├── engineer_features() ──► [84-step daily seq, static feats, XGB feats]
        │
        ├── LSTM (56K params) ────────────────► yield, failure_prob, attention (84 weights)
        ├── XGBoost Regressor (500 trees) ────► yield
        ├── XGBoost Classifier (500 trees) ───► failure_prob
        │
        └── Stacking Meta-Learner ──► Ensemble(yield) = 0.2×LSTM + 0.8×XGB
                                         Ensemble(fail)   = 0.68×LSTM + 0.32×XGB
```

## Models

### 1. LSTM + Attention (`predict.py:21-52`)
- **Architecture**: 2-layer LSTM (64 hidden), LayerNorm + learnable pos_bias attention, `nn.Embedding(30,8)` district embedding
- **Input**: 84-step daily weather sequence (4 vars: PRECTOTCORR, T2M, RH2M, GWETROOT) + static feats [d_idx, s_hot0, s_hot1, yr_offset]
- **Output**: Yield (regression), Failure logit (binary), Attention weights (84 timesteps)
- **Weights**: `models/lstm_final.pth` (56 K params)
- **Config**: `models/lstm_config.pth`
- **Pre-trained encoder**: `models/autoencoder_complete.pt` (118K params, masked autoencoder on 45 years of NASA telemetry)
- **Inference**: Weekly input (12×4) is upsampled to 84-daily via `weekly_to_daily()` repeating each week 7×
- **Training**: 150 epochs max, graduated unfreezing (encoder frozen 10 epochs, then LR/5)

### 2. XGBoost Regressor (`predict.py:169-170`)
- **Config**: 500 trees, max_depth=4, `monotone_constraints` enforced for correct directional response
- **Input**: 23 engineered features (4 vars × 4 stats + 3 critical-week aggregations + THI + 3 meta-features)
- **Output**: Yield (regression)
- **Weights**: `models/xgb_regressor.json`
- **Feature order** (must match `prepare_data.py` and `predict.py:122-142`):
  1-4: mean, std(ddof=1), max, min of PRECTOTCORR
  5-8: mean, std(ddof=1), max, min of T2M
  9-12: mean, std(ddof=1), max, min of RH2M
  13-16: mean, std(ddof=1), max, min of GWETROOT
  17: PRECTOTCORR sum over weeks 4-10
  18: T2M mean over weeks 4-10
  19: GWETROOT mean over weeks 4-10
  20: THI (T2M_mean × RH2M_mean / 100)
  21: district_encoder index
  22: season_encoder index
  23: year_offset (year - 2006)

### 3. XGBoost Classifier (`predict.py:172-173`)
- **Config**: 500 trees, max_depth=4, `scale_pos_weight` for class imbalance
- **Input**: Same 23 features as regressor
- **Output**: Failure probability (binary classification)
- **Weights**: `models/xgb_classifier.json`

### 4. Stacking Meta-Learner (`train.py:298-358`)
- **Method**: Convex weight grid search over validation set (87 samples), bounds fixed to [0.2, 0.8]
- **Yield weights**: LSTM=0.2, XGB=0.8 (implemented as `Ridge(alpha=0)` with coef_ set directly)
- **Failure weights**: LSTM=0.68, XGB=0.32
- **Weights**: `models/meta_yield.pkl`, `models/meta_fail.pkl`

## Data Flow

### Feature Engineering (`predict.py:101-142`)
1. Reshape 48-dim flat vector → 12×4 weekly matrix
2. Upsample to 84×4 daily sequence via `weekly_to_daily()` (repeat each week 7×)
3. Build static features: [district_idx, season_onehot_0, season_onehot_1, year-2006]
4. Compute 23 XGBoost features from weekly data (mean/std/max/min per var + critical weeks + THI + meta-features)
5. Scale LSTM seq with `seq_scaler.pkl`, XGB feats with `xgb_scaler.pkl`

### Predictor Singleton (`predict.py:146-322`)
- `CDTPredictor.predict()`: Runs LSTM + XGBoost + stacking + triggers → returns dict
- `CDTPredictor.monte_carlo()`: 500 forward passes with dropout enabled → stacked via meta-learner → CI + distribution

## Orchestrator (`orchestrator.py`)

### Query Types

| Query Type | Nodes Executed | Use Case |
|---|---|---|
| `yield_forecast` | `xgb_yield` | Fast single-model yield |
| `failure_risk` | `xgb_failure` + `triggers` | Binary risk assessment |
| `temporal_analysis` | `lstm_attention` + `triggers` | Attention patterns |
| `what_if` | `mc_dropout` + `xgb_yield` | Simulation uncertainty |
| `full_diagnosis` | All 5 nodes | Complete prediction |

### Response Assembly (`orchestrator.py:152-208`)
- When both LSTM and XGB outputs exist → uses stacking meta-learner (`yield_source: stacked_ensemble`)
- Falls back to raw model output if only one is available
- MC Dropout distribution + 90% CI included when `mc_dropout` node runs
- Attention weights included when `lstm_attention` node runs

### Performance

| Metric | Value | Model |
|--------|-------|-------|
| LSTM Yield R² | 0.636 | LSTM |
| LSTM Failure AUC | 0.782 | LSTM |
| XGB Regressor R² | 0.736 | XGBoost |
| XGB Classifier AUC | 0.801 | XGBoost |
| Stacked Ensemble R² | 0.737 | Meta-learner |
| Stacked Failure AUC | 0.814 | Meta-learner |

### Data

- **Training data**: `sources/data/final_dataset.csv` (1,083 rows, 30 districts, 2006-2024, zero interpolated)
- **Telemetry**: `sources/data/telemetry/*.csv` (30 files, 16,587 rows each, 1981-2026 daily NASA POWER)
- **Split**: Random 80/10/10 (train/val/test). Validation used for stacking calibration only — no test leakage.
- **Seasons**: Kharif (Jun 15 – Sep 6, 84 days), Rabi (Nov 1 – Jan 23, 84 days)
- **Year encoding**: Absolute offset `year - 2006` (range 0-18)

### Files

| File | Purpose |
|------|---------|
| `train.py` | Full training pipeline: LSTM→XGBoost→stacking |
| `predict.py` | CDTPredictor class, LSTMAttention, feature engineering, triggers, MC Dropout |
| `orchestrator.py` | DAG router, 5 nodes, 5 query types, stacking-aware response compilation |
| `prepare_data.py` | Data loading, daily sequence extraction, 80/10/10 split, scaling |
| `pretrain_autoencoder.py` | Masked autoencoder pre-training on 2,700 daily sequences |
| `prepare_pretrain_data.py` | Extracts 84-step sequences from telemetry CSVs |
| `validate_models.py` | 8-scenario validation suite + MC + directional stress tests |
| `models/` | All trained weights (see below) |
| `prepared_data/` | Preprocessed arrays + scalers + encoders |

### Model Files (`models/`)

| File | Purpose | Always needed? |
|------|---------|----------------|
| `lstm_final.pth` | LSTM fine-tuned weights | Yes |
| `lstm_config.pth` | LSTM architecture config | Yes |
| `lstm_best.pt` | LSTM best checkpoint (fallback if lstm_final missing) | Nice-to-have |
| `autoencoder_complete.pt` | Pre-trained autoencoder (for re-training only) | No (training only) |
| `autoencoder_best.pt` | Autoencoder best checkpoint | No (training only) |
| `xgb_regressor.json` | XGBoost yield regressor | Yes |
| `xgb_classifier.json` | XGBoost failure classifier | Yes |
| `meta_yield.pkl` | Stacking weight for yield (Ridge) | Yes |
| `meta_fail.pkl` | Stacking weight for failure (Ridge) | Yes |
| `lstm_attention.pth` | Old weekly model (7K params) | No (archived) |
| `lstm_attention_config.pth` | Old weekly config | No (archived) |

### Pre-trained Data (`prepared_data/`)

| File | Shape | Purpose |
|------|-------|---------|
| `X_seq_daily_{train,val,test}.npy` | (869,84,4) / (108,84,4) / (109,84,4) | 84-step daily sequences |
| `X_static_{train,val,test}.npy` | (869,4) / (108,4) / (109,4) | Static features |
| `X_xgb_{train,val,test}.npy` | (869,23) / (108,23) / (109,23) | XGBoost features (pre-scaled) |
| `y_yield_{train,val,test}.npy` | (869,) / (108,) / (109,) | Yield targets |
| `y_fail_{train,val,test}.npy` | (869,) / (108,) / (109,) | Failure targets |
| `seq_scaler.pkl` | — | StandardScaler for daily sequences |
| `xgb_scaler.pkl` | — | StandardScaler for XGB features |
| `district_encoder.pkl` | — | LabelEncoder (30 districts) |
| `season_encoder.pkl` | — | LabelEncoder (Kharif/Rabi) |
| `season_ohe.pkl` | — | OneHotEncoder for season |
| `district_ohe.pkl` | — | Legacy (unused) |

## Model Selection Rationale

### LSTM + Attention
84-step daily weather is sequential data where each timestep depends on the previous one. LSTM handles long sequences (84 days × 4 vars) without vanishing gradients. The attention mechanism lets the model dynamically focus on the most important growth phase (reproductive window, weeks 4-6) rather than treating all days equally. Pre-training on 45 years of unlabeled NASA telemetry transfers general weather dynamics knowledge before fine-tuning on the small labeled set (869 samples).

### XGBoost Regressor / Classifier
After engineering 23 tabular features from the raw weather (per-variable mean/std/max/min, critical-week aggregations, THI), the problem becomes tabular regression/classification. XGBoost is the gold standard for tabular data with <10K samples — it handles mixed feature types, has native regularization (prevents overfitting on 869 rows), and supports `monotone_constraints` which encode domain knowledge directly into the model (more rain → higher yield, higher temperature → lower yield). Feature importance also provides built-in explainability for which weather factors drove the prediction.

### Stacking Meta-Learner
LSTM captures temporal patterns (when rain falls matters) while XGBoost captures distributional patterns (how much rain fell overall). These are complementary. A convex weight blend (single scalar per task) was chosen over a full meta-model because: (a) only 2 parameters to estimate → minimal overfitting risk, (b) interpretable — you can inspect which model dominates, (c) bounds [0.2, 0.8] enforced to prevent ensemble collapse where one model gets zero weight.

### Monte Carlo Dropout
Standard neural networks produce point estimates with no uncertainty. MC Dropout reuses the trained LSTM's existing dropout layers at inference (500 forward passes) to produce a predictive distribution. This avoids training a separate Bayesian model. Stacking blends each MC sample with the deterministic XGBoost prediction, giving principled confidence intervals backed by both models.

### Weekly→Daily Upsampling
The API contract accepts 48-dim weekly weather for backward compatibility, but the LSTM was pre-trained on 84-step daily sequences from 45 years of NASA data. Repeating each week 7× is a linear interpolation that preserves the weekly pattern while matching the model's native resolution. If real daily telemetry ever becomes available at inference time, no code change is needed — it slots directly into the 84-step input.

## Critical Rules

1. **LSTMAttention class** exists in BOTH `train.py` and `predict.py`. Changes to one MUST be mirrored in the other, then re-train.
2. **Feature order** must stay synchronized: `predict.py:122-142` must match `prepare_data.py:79-105`.
3. **Static features** = `[d_idx, s_hot[0], s_hot[1], yr_offset]` everywhere. yr_offset = `year - 2006` (absolute, NOT normalized).
4. **Stacking weights** = grid search on validation set (NOT test), bounds [0.2, 0.8].
5. **XGBoost monotone_constraints** = `(1,0,1,1,-1,0,-1,-1,0,0,0,0,1,0,1,1,1,-1,1,0,0,0,1)` — enforces:
   - Precip mean/max/min: positive (more rain → higher yield)
   - Precip std: negative (erratic rain → lower yield)
   - Temp mean/max: negative (heat → lower yield)
   - Wetness mean/min/max: positive (wet soil → higher yield)
   - THI: negative (heat+humidity → lower yield)
   - District: positive (higher-index districts tend higher-yield)
   - Year: positive (technology trend)
   - Critical-week precip sum: positive
   - All other features: no constraint (0)
6. **Biophysical triggers** (`predict.py:56-93`): Rule-based, not learned. Four types: Submergence Flooding (W1-5 precip>250mm), Drought Stress (W3-8 wetness<0.35 for ≥3 weeks), Thermal Sterility (W7-9 temp>34°C), Pest/Pathogen Risk (RH>85% + 25°C≤temp≤30°C for ≥2 weeks).
7. **Cold-start districts** raise `ValueError` with valid district list — do NOT silently default.
8. **Rabi window** = Nov 1–Jan 23 (NOT Jan 1–Mar 25). Kharif = Jun 15–Sep 6.
9. **MC Dropout** runs 500 samples with dropout enabled, blends via stacking meta-learner, returns 5th/95th percentile CI.
