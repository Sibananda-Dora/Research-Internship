# Prediction Engine: Dual-Model Ensemble

The core prediction engine of the Cognitive Digital Twin (CDT), replacing the earlier Track-A/Track-B split. Sits within **Layer 3: Cognitive Analytics Layer** of the [[Cognitive Digital Twin — Architecture]].

## Evaluation Summary

After comprehensive benchmarking, the LSTM-Attention approach (former Track B) was **removed** — it achieved R²=0.048 (effectively random) and F1=0.00 on failure classification. The weather-only signal is too weak for a 12K-parameter recurrent model.

The new architecture uses a **dual-model ensemble** optimized for Monte Carlo simulation:

| Model | Role | Yield RMSE | Yield R² | Failure F1 | Failure AUC |
|---|---|---|---|---|---|
| **XGBoost** | Primary (fast, accurate) | 4.56 | 0.314 | 0.667 | 0.873 |
| **Deep NN + MC Dropout** | Secondary (uncertainty) | 4.60 | 0.302 | 0.623 | 0.878 |
| **Ensemble** | Final prediction | ~4.58 | ~0.31 | ~0.65 | ~0.88 |

## Feature Engineering (72 Features)

The key insight: weather features alone (48 weekly columns) have very low correlation with yield (max r=0.16). The model adds **24 engineered features**:

### Categorical / Temporal (3)
- `District_enc` — label-encoded district ID (30 districts)
- `Season_enc` — Kharif(0) / Rabi(1)
- `Year_scaled` — normalized to [0, 1] across 2006–2025

### Aggregated Weather Stats (16)
For each of the 4 variables (PRECTOTCORR, T2M, RH2M, GWETROOT):
- `mean` — 12-week average
- `std` — intra-season variability
- `max` — extreme event indicator
- `min` — baseline stress indicator

### Critical Period Features (3)
Weeks 4–10 (reproductive phase where crop is most sensitive):
- `precip_critical` — total precipitation over critical window
- `temp_critical` — mean temperature over critical window
- `wetness_critical` — mean soil wetness over critical window

### Interaction Features (2)
- `temp_humidity_stress` — T2M_mean × RH2M_mean (pest risk proxy)
- `precip_wetness_interaction` — PRECTOTCORR_mean × GWETROOT_mean (water-logging proxy)

## Primary Model: XGBoost

```
Hyperparameters:
  n_estimators=500, max_depth=4, learning_rate=0.05
  subsample=0.8, colsample_bytree=0.8
  reg_alpha=1.0, reg_lambda=2.0
```

- Handles non-linear interactions natively
- Robust to outliers (Rabi season has extreme yield values up to 170 Q/Acre)
- Fast inference: sub-millisecond per sample, enabling 1000+ Monte Carlo iterations
- Feature importance reveals `GWETROOT_max`, `Year_scaled`, and `W1_T2M` as top predictors

## Secondary Model: Deep Multi-Task NN with MC Dropout

```
Architecture:
  Input(72) → Linear(128) → BN → ReLU → Dropout(0.15)
           → Linear(64)  → BN → ReLU → Dropout(0.15)
           → Linear(32)  → BN → ReLU → Dropout(0.15)
           → Yield Head: Linear(32→16→1)
           → Failure Head: Linear(32→16→1)
```

**Monte Carlo Dropout**: During inference, dropout remains active. Each forward pass produces a different stochastic sample. N=500 passes yield a full predictive distribution:
- Mean = expected yield / failure probability
- Std = prediction uncertainty
- 90% CI = [5th percentile, 95th percentile]

This replaces the previous manual Monte Carlo approach with a principled Bayesian approximation — at **zero additional computational cost** since it reuses the same forward pass.

## Usage

```python
from predict import CDTPredictor

predictor = CDTPredictor()

# Single prediction
result = predictor.predict(weather_48_vector, district, season, year)

# Monte Carlo (returns distribution)
mc = predictor.monte_carlo(weather_48_vector, district, season, year, n_samples=500)
```

## Sources
- [[CPDT-Crop-Failure-Prediction Spec]]
- [[Comparative Analysis-2026]]
