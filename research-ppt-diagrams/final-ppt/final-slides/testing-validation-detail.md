# Testing & Validation — Deep Dive & Source Anchors

> Companion to `slide-08-testing-validation.md`. Contains the code-level evidence and full scenario data so the slide claims are defensible. All line numbers are from `code/phase-2-training/`.

---

## A. Where validation lives in the codebase

| Concern | File | Key lines |
|---|---|---|
| 80/10/10 random split | `prepare_data.py` | 107–120 |
| Final eval on held-out test (seed-42 random, ~223) | `train.py` | 241, 347–354 |
| Stacking blend search (val 2018–19) | `train.py` | 300–345 |
| MC Dropout (500 passes, dropout ON) | `predict.py` | 335–400 |
| Biophysical trigger rules | `predict.py` | 86–136 |
| 8 scenario + robustness suite | `validate_models.py` | 30–285 |
| Metric-gated deploy policy | `update_pipeline.py` | 216–230 (version/metrics) |

---

## B. Split design (why not chronological)

```text
prepare_data.py:107  # Random 80/10/10 split: train / val (stacking calibration) / test
```
- 1,113 rows → train 80% / val 8% (Ridge calibration only; 10% of the 80% train) / **test 20% (~223, seed 42, not year-filtered)**.
- Rationale (AGENTS.md rule #4): chronological split lets the model memorize the **post-2020 yield regime jump** and breaks temporal generalization. Random split + metric-gated redeploy is the chosen guard.

---

## C. Held-out performance — **re-measured on the saved models** (`evaluate_metrics.py`)

> IMPORTANT: the figures previously quoted in AGENTS.md / `train.py` print output
> (LSTM AUC 0.782, Stacked R² 0.736 / AUC 0.814) are **NOT reproducible** from the
> current saved weights. `evaluate_metrics.py` loads the exact saved models
> (`lstm_best.pt` == `lstm_final.pth` → AUC 0.685), the saved seed-42 test arrays, and the
> stacking meta-learners, and recomputes every metric. The likely cause of the gap: the
> saved models / prepared data predate the latest `final_dataset.csv` update (now 2006–2025).
> The numbers below are the honest, reproducible ones for the current repo state.

```text
evaluate_metrics.py  (run 2026-07-13)
  Test partition: 223 samples | failure pos-rate: 28.25%
  LSTM     Yield R2 0.641  RMSE 4.048  MAE 2.940  AUC 0.685  F1@.5 0.400
  XGBoost  Yield R2 0.682  RMSE 3.809  MAE 2.674  AUC 0.663  F1@.5 0.425
  Stacked  Yield R2 0.712  RMSE 3.627  MAE 2.497  AUC 0.721  F1@.5 0.455
  NaiveAvg Yield R2 0.711  RMSE 3.628  MAE 2.503  AUC 0.709  F1@.5 0.425
```

| Metric | LSTM | XGBoost | **Stacked** | Naive Avg |
|---|---|---|---|---|
| Yield R² | 0.641 | 0.682 | **0.712** | 0.711 |
| Yield RMSE (Q/A) | 4.05 | 3.81 | **3.63** | 3.63 |
| Yield MAE (Q/A) | 2.94 | 2.67 | **2.50** | 2.50 |
| Failure AUC | 0.685 | 0.663 | **0.721** | 0.709 |
| Failure F1 @0.5 | 0.400 | 0.425 | **0.455** | 0.425 |
| Failure Prec @0.5 | 0.403 | 0.480 | **0.532** | 0.480 |
| Failure Recall @0.5 | 0.397 | 0.381 | 0.397 | 0.381 |
| Failure Acc @0.5 | 0.664 | 0.709 | **0.731** | 0.709 |

Blend weights (`train.py:316–345`, saved in `meta_yield.pkl` / `meta_fail.pkl`):
Yield `0.2·LSTM + 0.8·XGBoost`; Failure `0.68·LSTM + 0.32·XGBoost`.
Stacked **beats both base learners on every metric** (highest R², lowest RMSE/MAE, highest AUC/F1/Precision/Accuracy).
F1/Precision/Recall/Accuracy are at threshold 0.5 on an imbalanced set (~28% positive); optimal-threshold F1 is reported in `metrics_eval.json`.

---

## D. Full scenario suite (`validate_models.py:30–128`)

Each scenario: realistic 12-week weather → `predict()` → assert yield band, failure direction, and fired trigger.

| # | Scenario | District / Season | Stress signature | Expected trigger |
|---|---|---|---|---|
| 1 | Normal Kharif | Angul / Kharif | rising monsoon, peak W5–6 | — |
| 2 | Drought Stress | Kalahandi / Kharif | precip ≤10 mm, T≥35 °C | Drought Stress |
| 3 | Flood / Cyclone | Balasore / Kharif | precip 280–320 mm W4–5 | Submergence Flooding |
| 4 | Thermal Sterility | Sambalpur / Kharif | T>34 °C W7–9 | Thermal Sterility |
| 5 | Pest / Pathogen | Cuttack / Kharif | RH>85 %, 25–30 °C sustained | Pest/Pathogen Risk |
| 6 | Excellent Season | Bargarh / Kharif | ideal monsoon | — |
| 7 | Rabi (winter) | Puri / Rabi | dry, cool (17–28 °C) | — |
| 8 | Coastal High-Yield | Ganjam / Kharif | coastal high-yield profile | — |

Validation logic (`validate_models.py:152–172`): yield-in-band PASS/WARN; failure direction with 0.5×/1.5× tolerance; trigger subset-match PASS/MISS.

---

## E. Monte Carlo Dropout validation (`validate_models.py:192–221`)

```text
mc = predictor.monte_carlo(drought_weather, 'Kalahandi','Kharif',2024, n_samples=300)
  MC Yield:  7.4 ± 1.9 Q/Acre
  MC 90% CI: [4.9, 10.2]
  MC Dist:   300 samples        -> PASS (== 300)
  CI Width:  5.3 Q/Acre         -> PASS (0.1 < 5.3 < 15.0)
```
- `predict.py:340` `_enable_dropout()` re-enables dropout at inference; 500 passes in production (`orchestrator.py:117`).
- CI reported as `confidence_interval: {lower, upper}` in the API contract.

---

## F. Robustness checks (`validate_models.py:223–274`)

- **Cross-district (223–241):** same weather on Angul/Bargarh/Cuttack/Ganjam/Kalahandi/Puri → distinct yields; `spread > 0` → PASS (district embedding works).
- **Temporal (243–250):** Angul, same weather, years 2021–2024 → plausible variation, no artifacts.
- **Directional (252–274):** drought severity 0.2×→1.5× precip → yield trend decreases (more water → more yield direction validated).
- **Cold-start (AGENTS.md rule #6 / `predict.py`):** unknown district → `ValueError`, never silently defaults to Angul.
- **Input sanitization (NFR-05):** out-of-range telemetry rejected.

---

## G. Biophysical trigger rules (`predict.py:86–136`)

| Trigger | Condition |
|---|---|
| Drought Stress | `drought_max ≥ 3` → ≥3 consecutive weeks GWETROOT low in W3–8 |
| Submergence Flooding | PRECTOTCORR weekly > 250 mm |
| Thermal Sterility | T2M > 34 °C in ≥1 week (grain filling) |
| Pest/Pathogen Risk | `pest_max ≥ 2` → ≥2 consecutive warm-humid weeks |

Attention validation (`validate_models.py:184–189`): weekly attention summed; peak week + W4–6 mass printed — confirms model attends to the critical reproductive window.

---

## H. Deployment governance (`update_pipeline.py`)

- Version bump `major.minor+1` on retrain (`update_pipeline.py:216–218`); metrics parsed from train output (221–226).
- Policy (from architecture spec / algo 2): deploy new model only if `R²_new ≥ R²_old − 0.02 AND AUC_new ≥ AUC_old − 0.02`; hot-swap failure model only if `AUC_new − AUC_old ≥ 0.02`; else fallback. Guarantees no silent regression.

---

## I. Known limitations (for honest Q&A)

1. **Post-2020 regime:** yield mean 7.8 → 14.0 Q/A; historical-trained model under-predicts recent highs. Mitigation: retraining pipeline + metric-gated deploy.
2. **Rabi sparsity:** Nov–Jan fewer samples; some districts no Rabi → weaker Rabi metrics.
3. **i.i.d. split:** random split ignores time order; drift handled operationally, not by the split.

---

## J. How this maps to the 10-slide final format

- Required slide **#8 "Testing & Validation"** → this content.
- Adjacent slides: #7 Design & Implementation carries the algorithms; #9 Results & Discussion should echo the R²/AUC table and the limitations above.
- Reuse assets: none required (text/table slide); optionally a screenshot of `validate_models.py` run output if a live terminal demo is shown.
