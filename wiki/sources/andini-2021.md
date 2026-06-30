# Source: Climate Prediction Using RNN LSTM (Andini & Utomo, 2021)

**Title**: Climate Prediction Using RNN LSTM to Estimate Agricultural Products Based on Koppen Classification
**Status**: Analyzed

## Key Findings
- **Model**: RNN-LSTM (48 input neurons).
- **Metric**: Achieved a MAPE of 3.29% for 1-month-ahead climate forecasting.
- **Optimization**: Adam optimizer with 200 epochs is the optimal configuration.

## Relevance to CPDT
- Provides a baseline for **Temporal Scaling**—1 month is the standard, but we are extending to a 12-week tensor.
- Köppen Classification provides a secondary validation layer for our regional suitability engine.

## Research Gaps Addressed by CPDT
- **Temporal Depth**: We are moving beyond 1-month predictions to full-season (12-week) trajectories.
- **Feature Depth**: We include Root Soil Wetness (`GWETROOT`) which they omitted.

## Sources
- `sources/papers/Climate Prediction Using RNN LSTM to Estimate Agricultural Products Based on Koppen Classification.pdf`
