## Model Performance Metrics (Test Set 2020-2024)

| Model | Yield R² | Failure AUC | Blend Weight (Yield) | Blend Weight (Failure) |
|-------|----------|-------------|---------------------|----------------------|
| LSTM+Attention (84-step daily) | 0.636 | 0.782 | 0.20 | 0.68 |
| XGBoost (23 features, 500 trees) | 0.736 | 0.801 | 0.80 | 0.32 |
| **Stacking (val-calibrated)** | **0.736** | **0.814** | — | — |

### Why these models?

**LSTM+Attention** — Captures temporal weather patterns (monsoon onset, dry spells, heat waves) across 84 daily timesteps. Attention highlights critical weeks (4-6: flowering/grain-filling stage).

**XGBoost** — Handles static features (district, season) and aggregated weekly statistics. Best single-model yield R² (0.736) by capturing non-linear interactions between static variables.

**Stacking** — Calibrated on chronological validation (2018-2019) via weight sweep (61 points). Yield favors XGBoost 0.8 (better magnitude), failure favors LSTM 0.68 (better risk detection). Both models contribute complementary signal.

### Data Split
- Train: 80% (random)
- Validation: 10% (for stacking calibration)
- Test: 10% (held-out, years ≥ 2020)
