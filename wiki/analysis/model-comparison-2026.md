# Model Comparison & Architecture Decision (2026)

## Background
The CDT prediction engine was evaluated under two competing architectures: the original Track-A (Random Forest on flattened weather) / Track-B (LSTM-Attention on 3D tensor) split, and a proposed dual-model ensemble (XGBoost + Deep NN with MC Dropout on 72 engineered features).

## Benchmark Results

| Model | Features | Yield RMSE | Yield R² | Failure F1 | Failure AUC |
|---|---|---|---|---|---|
| **Track A: Random Forest** | Weather only (48) | 4.52 | 0.324 | 0.561 | 0.799 |
| **Track B: LSTM-Attention** | Weather 3D tensor (12×4) | **5.37** | **0.048** | **0.000** | **0.537** |
| XGBoost | Weather only (48) | 4.18 | 0.424 | 0.633 | 0.832 |
| Enhanced XGBoost | 72 engineered | 4.56 | 0.314 | 0.667 | 0.873 |
| Deep NN + MC Dropout | 72 engineered | 4.60 | 0.302 | 0.623 | 0.878 |

## Key Findings

### 1. Track-B LSTM-Attention is ineffective
R²=0.048 means the model explains virtually none of the yield variance. F1=0.00 on failure classification means it never identified a failure correctly. The 12-week weather sequence lacks sufficient signal for a recurrent model with 12K parameters. Training loss barely decreased over 100 epochs.

### 2. Weather features alone are weak predictors
Max correlation with yield is r=0.16 (Week 6 Temperature). The yield variance is primarily driven by district-level factors, seasonal differences, and long-term trends — not weekly weather patterns.

### 3. Feature engineering is the biggest unlock
Adding District, Season, Year, aggregated stats, and critical-period features improved Failure AUC from 0.83 → 0.88 and F1 from 0.63 → 0.67. XGBoost feature importance confirms `GWETROOT_max`, `Year_scaled`, and `W1_T2M` as top predictors.

### 4. MC Dropout provides free uncertainty
The Deep NN with MC Dropout gives a full predictive distribution (mean ± std, 90% CI) at no extra computational cost — simply by keeping dropout active during inference.

## Decision
Replaced Track-A/Track-B with the dual-model ensemble pipeline in `/code/phase-2-training/`.

## Sources
- [[CPDT-Crop-Failure-Prediction Spec]]
- [[Prediction Engine: Dual-Model Ensemble]]
